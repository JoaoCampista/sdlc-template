import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2]


def feature(identifier='F-EXAMPLE-V1', status='in_review'):
    return f'''---
id: {identifier}
kind: feature_spec
title: Example
parent: PROD-001
version: 0.1.0
status: {status}
last_updated: 2026-10-26
---
## WHAT/HOW
One observable behavior.
## User Stories
- User can use it.
## Acceptance Criteria
- **AC-1.** Works. @test:tests/example.py
## NFRs
Hermetic.
## NEEDS_CLARIFICATION
- nenhum
'''


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sdd test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        for path in ('scripts/sdd', '.claude/hooks'):
            shutil.copytree(SOURCE / path, self.root / path, ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy(SOURCE / 'scripts/setup.sh', self.root / 'scripts/setup.sh')
        shutil.copy(SOURCE / 'scripts/doctor.sh', self.root / 'scripts/doctor.sh')
        shutil.copy(SOURCE / '.claude/settings.json', self.root / '.claude/settings.json')
        (self.root / '.gitignore').write_text('.sdd/\n__pycache__/\n')
        (self.root / '.specs/features/F-EXAMPLE-V1').mkdir(parents=True)
        (self.root / '.specs/features/F-EXAMPLE-V1/spec.md').write_text(feature())
        (self.root / '.specs/postmortems').mkdir()
        (self.root / '.specs/product').mkdir()
        (self.root / '.specs/product/product-spec.md').write_text('---\nid: PROD-001\nkind: product_spec\ntitle: Product\nparent: CONST-001\nversion: 0.1.0\nstatus: draft\nbootstrap: pending\nlast_updated: 2026-10-26\n---\n')
        (self.root / 'tests').mkdir()
        (self.root / 'tests/example.py').write_text('pass\n')
        (self.root / '.sdd').mkdir()
        (self.root / '.sdd/active-spec').write_text('')
        self.env = {k:v for k,v in os.environ.items() if not k.startswith(('GIT_', 'SDD_', 'CLAUDE_'))}
        self.env.update(CLAUDE_PROJECT_DIR=str(self.root), PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-q')
        # Isolated fixture identity; never changes real user/repository configuration.
        self.git('config', 'user.name', 'SDD Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.run_script('scripts/sdd/spec-index.sh')

    def run_cmd(self, args, ok=True, data=None, env=None, cwd=None):
        result = subprocess.run(args, cwd=cwd or self.root, env=env or self.env, input=data, text=True, capture_output=True)
        if ok: self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def git(self, *args, **kw):
        return self.run_cmd(['git', *args], **kw)

    def run_script(self, path, *args, **kw):
        return self.run_cmd(['bash', str(self.root / path), *args], **kw)

    def activate(self, status='in_review'):
        (self.root / '.sdd/active-spec').write_text('F-EXAMPLE-V1\n')
        (self.root / '.specs/features/F-EXAMPLE-V1/spec.md').write_text(feature(status=status))

    def hook(self, script, payload, ok=True):
        return self.run_script('.claude/hooks/' + script, data=json.dumps(payload), ok=ok)

    def baseline(self):
        self.git('add', '.specs', 'scripts', '.claude', '.gitignore', 'tests')
        self.git('commit', '-qm', 'chore: fixture baseline')

    def install(self):
        self.run_script('scripts/sdd/install-git-hooks.sh')
