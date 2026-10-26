import json
import os
from pathlib import Path
import shutil
from support import RepoCase, SOURCE, feature


class Tooling(RepoCase):
    def test_index_is_deterministic_and_atomic(self):
        """AC-2: content/mtime stable; duplicate does not replace the good index."""
        path = self.root / '.specs/index.json'
        original, stamp = path.read_bytes(), path.stat().st_mtime_ns
        self.run_script('scripts/sdd/spec-index.sh')
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (original, stamp))
        (self.root / '.specs/duplicate.md').write_text(feature())
        self.assertNotEqual(self.run_script('scripts/sdd/spec-index.sh', ok=False).returncode, 0)
        self.assertEqual(path.read_bytes(), original)

    def test_drift_detects_edit_add_delete_metadata_and_bad_json(self):
        """AC-2: drift compares full artifact metadata and bytes, fails closed."""
        path = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        original = path.read_text()
        path.write_text(original + '\nchanged\n')
        self.assertNotEqual(self.run_script('scripts/sdd/spec-drift.sh', ok=False).returncode, 0)
        path.write_text(original)
        other = self.root / '.specs/extra.md'
        other.write_text(feature('F-OTHER-V1'))
        self.assertNotEqual(self.run_script('scripts/sdd/spec-drift.sh', ok=False).returncode, 0)
        other.unlink()
        path.unlink()
        self.assertNotEqual(self.run_script('scripts/sdd/spec-drift.sh', ok=False).returncode, 0)
        path.write_text(original)
        index = self.root / '.specs/index.json'
        content = json.loads(index.read_text()); content['artifacts'][0]['status'] = 'deprecated'
        index.write_text(json.dumps(content))
        self.assertNotEqual(self.run_script('scripts/sdd/spec-drift.sh', ok=False).returncode, 0)
        index.write_text('{broken')
        self.assertNotEqual(self.run_script('scripts/sdd/spec-drift.sh', ok=False).returncode, 0)

    def test_setup_is_idempotent_preserves_identity_state_and_no_commit(self):
        """AC-1: no hidden commit or state reset."""
        self.activate()
        for _ in range(2): self.run_script('scripts/setup.sh')
        self.assertEqual((self.root / '.sdd/active-spec').read_text().strip(), 'F-EXAMPLE-V1')
        self.assertEqual(self.git('config', 'user.email').stdout.strip(), 'fixture@example.invalid')
        self.assertNotEqual(self.git('rev-parse', '--verify', 'HEAD', ok=False).returncode, 0)
        self.run_script('scripts/doctor.sh')

    def test_setup_preserves_foreign_hooks_and_custom_hookspath(self):
        """AC-1: foreign hooks remain byte identical."""
        hook = self.root / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\necho foreign\n')
        self.assertNotEqual(self.run_script('scripts/setup.sh', ok=False).returncode, 0)
        self.assertEqual(hook.read_text(), '#!/bin/sh\necho foreign\n')
        self.assertFalse((self.root / '.git/hooks/commit-msg').exists())
        hook.unlink()
        self.git('config', 'core.hooksPath', '.custom-hooks')
        self.assertNotEqual(self.run_script('scripts/setup.sh', ok=False).returncode, 0)
        self.assertEqual(self.git('config', 'core.hooksPath').stdout.strip(), '.custom-hooks')

    def test_setup_supports_worktree(self):
        """AC-1: .git file, isolated active-spec and correct hook location."""
        self.baseline()
        target = self.root.parent / 'other worktree'
        self.git('worktree', 'add', '-qb', 'fixture-other', str(target))
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(target))
        self.run_cmd(['bash', 'scripts/setup.sh'], cwd=target, env=env)
        self.assertTrue((target / '.git').is_file())
        self.run_cmd(['bash', 'scripts/doctor.sh'], cwd=target, env=env)

    def test_lint_design_tasks_status_and_approval(self):
        """AC-7: design is canonical, malformed tasks/status and approval rejected."""
        template = (SOURCE / '.specs/features/_TEMPLATE/design.md').read_text()
        template = template.replace('<DOMINIO>', 'EXAMPLE').replace('<YYYY-MM-DD>', '2026-10-26')
        import re
        template = re.sub(r'<[^>]+>', 'example', template)
        design = self.root / '.specs/features/F-EXAMPLE-V1/design.md'
        design.write_text(template)
        self.run_script('scripts/sdd/spec-lint.sh', str(design))
        self.run_script('scripts/sdd/spec-index.sh')
        self.assertIn('DESIGN-F-EXAMPLE-V1', json.loads((self.root / '.specs/index.json').read_text())['hashes'])
        self.activate('unexpected')
        self.assertNotEqual(self.run_script('scripts/sdd/spec-lint-all.sh', ok=False).returncode, 0)
        self.activate('approved')
        (self.root / 'tests/example.py').unlink()
        self.assertNotEqual(self.run_script('scripts/sdd/spec-lint-all.sh', ok=False).returncode, 0)
        self.activate()
        task = self.root / '.specs/tasks.md'
        task.write_text('---\nid: TASKS-F-EXAMPLE-V1\nkind: tasks\ntitle: Tasks\nparent: F-EXAMPLE-V1\nversion: 0.1.0\nstatus: draft\nlast_updated: 2026-10-26\n---\n| T-001 | missing AC | todo |\n')
        self.assertNotEqual(self.run_script('scripts/sdd/spec-lint-all.sh', ok=False).returncode, 0)

    def test_commit_validates_staged_content_not_worktree(self):
        """AC-6: disk fixed/stage broken fails, disk broken/stage valid succeeds."""
        self.baseline(); self.install(); self.activate()
        spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        original = spec.read_text()
        spec.write_text(original + '\nunstaged initially\n')
        self.git('add', '.specs/features/F-EXAMPLE-V1/spec.md')
        spec.write_text(original)
        self.assertNotEqual(self.git('commit', '-qm', 'feat: invalid stage', ok=False).returncode, 0)
        self.git('add', '.specs/features/F-EXAMPLE-V1/spec.md')
        (self.root / 'tests/example.py').write_text('pass\n# staged change\n')
        self.git('add', 'tests/example.py')
        spec.write_text(original + '\nnot in stage\n')
        self.git('commit', '-qm', 'feat: valid stage')
        import hashlib
        self.assertIn(hashlib.sha256(original.encode()).hexdigest(), self.git('log', '-1', '--format=%B').stdout)
        self.assertEqual(self.git('log', '-1', '--format=%s').stdout.strip(), 'feat: valid stage')

    def test_amend_refreshes_hash_preserves_refs(self):
        """AC-6: no stale hash on amend; task refs survive."""
        self.baseline(); self.install(); self.activate()
        spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        spec.write_text(spec.read_text() + '\nrevision\n')
        self.run_script('scripts/sdd/spec-index.sh'); self.git('add', '.specs')
        self.git('commit', '--amend', '-qm', 'feat: revised\n\nRefs: F-EXAMPLE-V1 AC-1 T-001\nSpec-Hash: sha256:old')
        message = self.git('log', '-1', '--format=%B').stdout
        self.assertEqual(message.count('Spec-Hash:'), 1)
        self.assertNotIn('sha256:old', message)
        self.assertIn('AC-1 T-001', message)
        self.assertEqual(self.git('log', '-1', '--format=%s').stdout.strip(), 'feat: revised')
        trailers = self.git('interpret-trailers', '--parse', data=message).stdout
        self.assertIn('Refs: F-EXAMPLE-V1 AC-1 T-001', trailers)
        self.assertIn('Spec-Hash:', trailers)

    def test_staged_validator_and_missing_spec_fail(self):
        """AC-6: use the staged validator, and fail if active spec absent from stage."""
        self.baseline(); self.install()
        script = self.root / 'scripts/sdd/spec-lint-all.sh'
        old = script.read_text()
        script.write_text('#!/bin/sh\nexit 1\n')
        self.git('add', 'scripts/sdd/spec-lint-all.sh'); script.write_text(old)
        self.assertNotEqual(self.git('commit', '-qm', 'test: staged validator', ok=False).returncode, 0)
        self.git('add', 'scripts/sdd/spec-lint-all.sh')
        self.activate()
        self.git('rm', '.specs/features/F-EXAMPLE-V1/spec.md')
        self.run_script('scripts/sdd/spec-index.sh'); self.git('add', '.specs/index.json')
        self.assertNotEqual(self.git('commit', '-qm', 'test: removed active spec', ok=False).returncode, 0)

    def test_prepush_checks_sent_revision_not_disk(self):
        """AC-6: clean disk cannot hide drift in pushed commit."""
        self.baseline()
        good = self.git('rev-parse', 'HEAD').stdout.strip()
        spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        spec.write_text(spec.read_text() + '\nbad committed spec\n')
        self.git('add', '.specs/features/F-EXAMPLE-V1/spec.md')
        self.git('commit', '-qm', 'test: invalid revision') # fixture before hooks installed
        bad = self.git('rev-parse', 'HEAD').stdout.strip()
        self.run_script('scripts/sdd/spec-index.sh')
        zeros = '0' * 40
        self.assertNotEqual(self.run_script('scripts/sdd/git-pre-push.sh', data=f'refs/heads/main {bad} refs/heads/main {zeros}\n', ok=False).returncode, 0)
        self.run_script('scripts/sdd/git-pre-push.sh', data=f'refs/heads/main {good} refs/heads/main {zeros}\n')
        self.run_script('scripts/sdd/git-pre-push.sh', data=f'(delete) {zeros} refs/heads/old {good}\n')

    def test_git_hook_ignores_foreign_session_root(self):
        """AC-6 regression: Git target, not parent assistant env, owns the stage."""
        self.baseline(); self.install()
        foreign = self.root.parent / 'foreign'
        import shutil
        shutil.copytree(self.root, foreign, ignore=shutil.ignore_patterns('.git', '.sdd'))
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(foreign))
        self.run_cmd(['git', 'init', '-q'], cwd=foreign, env=env)
        self.run_cmd(['git', 'add', '.specs', 'scripts', '.claude', 'tests', '.gitignore'], cwd=foreign, env=env)
        spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        spec.write_text(spec.read_text() + '\ninvalid stage\n')
        self.git('add', '.specs/features/F-EXAMPLE-V1/spec.md')
        self.assertNotEqual(self.git('commit', '-qm', 'feat: cross repo', env=env, ok=False).returncode, 0)
        self.run_script('scripts/sdd/spec-index.sh'); self.git('add', '.specs')
        (foreign / '.sdd').mkdir(); (foreign / '.sdd/active-spec').write_text('F-EXAMPLE-V1')
        self.git('commit', '-qm', 'feat: own repo', env=env)
        self.assertNotIn('Spec-Hash:', self.git('log', '-1', '--format=%B').stdout)

    def test_partial_placeholders_and_invalid_index_status(self):
        """AC-2/7: retain template lint coverage and preserve index on invalid metadata."""
        spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        for placeholder in ('<contrato técnico interno: interface, invariantes>', 'Como <papel>, quero <ação>, para <valor>.'):
            spec.write_text(feature() + '\n' + placeholder)
            self.assertNotEqual(self.run_script('scripts/sdd/spec-lint-all.sh', ok=False).returncode, 0)
        original = (self.root / '.specs/index.json').read_bytes()
        spec.write_text(feature(status='bogus'))
        self.assertNotEqual(self.run_script('scripts/sdd/spec-index.sh', ok=False).returncode, 0)
        self.assertEqual(original, (self.root / '.specs/index.json').read_bytes())
