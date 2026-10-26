import json
from pathlib import Path
import re
from support import RepoCase, SOURCE, feature


class Hooks(RepoCase):
    def edit(self, path, **kwargs):
        return self.hook('pre-edit-guard.sh', dict(tool_name='Write', cwd=str(self.root), tool_input=dict(file_path=str(path))), **kwargs)

    def bash(self, command, **kwargs):
        return self.hook('bash-guard.sh', dict(tool_name='Bash', cwd=str(self.root), tool_input=dict(command=command)), **kwargs)

    def action(self, result):
        return json.loads(result.stdout).get('hookSpecificOutput', {}).get('permissionDecision')

    def test_spec_status_missing_invalid_and_valid(self):
        """AC-3: deny all inactive/invalid states, including deprecated (not just draft)."""
        self.assertEqual(self.action(self.edit('src/app.py')), 'deny')
        for status in ('draft', 'deprecated', 'bogus', ''):
            self.activate(status)
            self.assertEqual(self.action(self.edit('src/app.py')), 'deny')
        for status in ('in_review', 'approved'):
            self.activate(status)
            self.assertIsNone(self.action(self.edit('src/app.py')))
        (self.root / '.sdd/active-spec').write_text('../bad')
        self.assertEqual(self.edit('src/app.py', ok=False).returncode, 2)

    def test_paths_symlinks_cwd_and_harness(self):
        """AC-3: classify the effective destination, preserve external temp files."""
        (self.root / 'src').mkdir()
        (self.root / 'docs').mkdir()
        (self.root / 'docs/alias.md').symlink_to(self.root / 'src/code.py')
        self.assertEqual(self.action(self.edit('docs/alias.md')), 'deny')
        self.assertEqual(self.action(self.edit('docs/../src/a.py')), 'deny')
        self.assertIsNone(self.action(self.edit('docs/guide.md')))
        self.assertIsNone(self.action(self.edit(self.root.parent / 'outside.txt')))
        self.assertEqual(self.action(self.edit('.specs/index.json')), 'deny')
        self.assertEqual(self.action(self.edit('.claude/hooks/guard.py')), 'ask')
        self.assertEqual(self.action(self.edit('.claude/settings.local.json')), 'ask')
        self.assertEqual(self.action(self.edit('.git/config')), 'deny')
        payload = dict(tool_name='Write', cwd=str(self.root / 'src'), tool_input=dict(file_path='a.py'))
        self.assertEqual(self.action(self.hook('pre-edit-guard.sh', payload)), 'deny')

    def test_invalid_input_fails_closed(self):
        """AC-3/5: invalid JSON/schema doesn't become an allow."""
        for script in ('pre-edit-guard.sh', 'bash-guard.sh', 'stop-check.sh', 'post-spec-edit.sh'):
            for raw in ('broken', '[]'):
                result = self.run_script('.claude/hooks/' + script, data=raw, ok=False)
                self.assertEqual(result.returncode, 2, script + result.stderr)
        self.assertEqual(self.hook('pre-edit-guard.sh', {'tool_input': {}}, ok=False).returncode, 2)
        self.assertEqual(self.hook('stop-check.sh', {'stop_hook_active': 'false'}, ok=False).returncode, 2)

    def test_bash_write_variants_and_read_contraposition(self):
        """AC-4: actual guard decisions, without executing the requested command."""
        commands = ['echo x > src/a.py', 'printf x >> src/a.py', 'tee src/a.py', 'cp docs/a.md src/a.py', 'touch src/a.py', 'mkdir src/new', 'mv docs/a.md src/a.py', 'sed -i x src/a.py', 'dd of=src/a.py', 'curl -o src/a.py https://example.invalid', 'bash -c "echo x > src/a.py"', 'cd src && touch a.py']
        for command in commands:
            self.assertEqual(self.action(self.bash(command)), 'deny', command)
        for command in ('git status --short', 'cat src/a.py', 'echo safe', 'echo x > docs/a.md'):
            self.assertIsNone(self.action(self.bash(command)), command)
        self.activate()
        self.assertIsNone(self.action(self.bash('echo x > src/a.py')))

    def test_bash_opaque_destructive_and_bypass(self):
        """AC-4: permissions for unknown effects, no silent bypass."""
        for command in ('python3 -c "print(1)"', 'bash custom.sh', 'eval echo x', 'docker compose down -v', 'rm data.db', 'git reset --hard', 'echo $(date)', 'psql -c "DROP TABLE users"'):
            self.assertEqual(self.action(self.bash(command)), 'ask', command)
        for command in ('git add -f __hook_probe_inexistente__', 'git commit -n -m x', 'git -c core.hooksPath=/tmp commit -m x', 'SDD_ALLOW_TRIVIAL=1 echo x', 'git add -A', 'git commit --no-verify'):
            self.assertEqual(self.action(self.bash(command)), 'deny', command)
        self.assertEqual(self.action(self.bash('echo x > .claude/settings.json')), 'ask')

    def test_stop_json_drift_and_loop(self):
        """AC-5: exactly one JSON object, never plain text on stdout."""
        self.assertEqual(json.loads(self.hook('stop-check.sh', {}).stdout), {})
        (self.root / '.specs/index.json').write_text('{}')
        self.assertEqual(json.loads(self.hook('stop-check.sh', {}).stdout)['decision'], 'block')
        repeat = self.hook('stop-check.sh', dict(stop_hook_active=True))
        self.assertEqual(json.loads(repeat.stdout), {})
        self.assertIn('DRIFT', repeat.stderr)

    def test_stop_consecutive_commits_reconciliation(self):
        """AC-5: an earlier spec commit must not hide a later sequence."""
        self.baseline()
        for i in range(3):
            path = self.root / 'tests/example.py'; path.write_text(f'# {i}\n')
            self.git('add', 'tests/example.py'); self.git('commit', '-qm', 'test: iteration')
        self.assertIn('GATILHO', json.loads(self.hook('stop-check.sh', {}).stdout)['reason'])
        spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'; spec.write_text(spec.read_text() + '\nreconciled\n')
        self.run_script('scripts/sdd/spec-index.sh'); self.git('add', '.specs'); self.git('commit', '-qm', 'docs: reconcile')
        self.assertEqual(json.loads(self.hook('stop-check.sh', {}).stdout), {})

    def test_post_edit_propagates_index_failure(self):
        """AC-5: a duplicate ID does not get swallowed by PostToolUse."""
        (self.root / '.specs/duplicate.md').write_text(feature())
        result = self.hook('post-spec-edit.sh', dict(cwd=str(self.root), tool_input=dict(file_path='.specs/duplicate.md')), ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('duplicate_id', result.stderr)

    def test_settings_wiring_and_no_product_configuration(self):
        """AC-8: every event executes the expected script; no copied product permissions."""
        settings = json.loads((SOURCE / '.claude/settings.json').read_text())
        expected = {'SessionStart': ['session-start.sh'], 'PreToolUse': ['pre-edit-guard.sh', 'bash-guard.sh'], 'PostToolUse': ['post-spec-edit.sh'], 'Stop': ['stop-check.sh']}
        for event, names in expected.items():
            commands = [hook['command'] for group in settings['hooks'][event] for hook in group['hooks']]
            self.assertEqual(len(commands), len(names))
            for name in names: self.assertTrue(any('/.claude/hooks/' + name in command for command in commands))
        for tool in ('Edit', 'Write', 'MultiEdit', 'NotebookEdit'):
            self.assertTrue(re.fullmatch(settings['hooks']['PreToolUse'][0]['matcher'], tool))
        self.assertTrue(re.fullmatch(settings['hooks']['PreToolUse'][1]['matcher'], 'Bash'))
        raw = json.dumps(settings)
        for banned in ('Spectrolite', '/Users/', 'enabledPlugins', 'Bash(python3 *)', 'Bash(npm *)', 'Bash(docker compose *)'):
            self.assertNotIn(banned, raw)

    def test_multiline_bash_preserves_command_boundaries(self):
        """AC-4 regression: newline commands must be checked like semicolons."""
        for command in ('echo safe\ntouch src/app.py', 'echo safe\ngit commit --no-verify', 'echo safe;\n\ntouch src/app.py'):
            self.assertEqual(self.action(self.bash(command)), 'deny', command)
        self.assertEqual(self.action(self.bash('echo safe\nrm data.db')), 'ask')
        self.assertIsNone(self.action(self.bash('echo "a\nb"')))

    def test_multiline_comments_require_review_and_crashes_block(self):
        """AC-3/4: preserve protection when shell comments or hook runtime fail."""
        for command in ('echo safe # check\ntouch src/a.py', 'echo safe # check\nrm data.db'):
            self.assertEqual(self.action(self.bash(command)), 'ask')
        (self.root / 'cycle').symlink_to(self.root / 'cycle')
        self.assertEqual(self.edit('cycle/a.py', ok=False).returncode, 2)
        self.activate()
        self.assertEqual(self.edit('cycle/a.py', ok=False).returncode, 2)
        (self.root / '.claude/hooks/guard.py').write_text('invalid python !')
        self.assertEqual(self.edit('src/a.py', ok=False).returncode, 2)

    def test_bootstrap_and_templates_are_product_independent(self):
        """AC-8: product/stack open, private paths and origin design not distributed."""
        product = (SOURCE / '.specs/product/product-spec.md').read_text()
        self.assertIn('bootstrap: pending', product)
        self.assertIn('Produto a definir', product)
        constitution = (SOURCE / '.specs/constitution/constitution.md').read_text()
        self.assertIn('a definir no bootstrap', constitution)
        for folder in (SOURCE / '.claude', SOURCE / '.specs/features/_TEMPLATE', SOURCE / '.specs/components/_TEMPLATE'):
            for path in folder.rglob('*'):
                if path.is_file() and path.suffix in ('.md', '.json', '.sh', '.py'):
                    content = path.read_text()
                    self.assertNotIn('/Users/', content, str(path))
                    self.assertNotIn('SPECTROLITE_', content, str(path))
                    self.assertNotIn('figma.com/design/', content, str(path))
