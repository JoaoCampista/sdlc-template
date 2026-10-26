#!/usr/bin/env python3
"""Targeted counterproofs in disposable copies. Run separately from the fast suite."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parents[2]
CASES = [
    ('guard removed', '.claude/hooks/guard.py', "reason = code_reason()", "reason = ''", 'test_hooks.Hooks.test_spec_status_missing_invalid_and_valid'),
    ('Stop emits text', 'scripts/sdd/sdd.py', "print('{}')", "print('not JSON')", 'test_hooks.Hooks.test_stop_json_drift_and_loop'),
    ('index timestamp', 'scripts/sdd/sdd.py', 'entries = catalog()', "entries = catalog()\n    entries['generated_at'] = __import__('time').time_ns()", 'test_tooling.Tooling.test_index_is_deterministic_and_atomic'),
    ('stage validation removed', 'scripts/sdd/sdd.py', "validate_tree(git('write-tree').decode().strip())", 'pass', 'test_tooling.Tooling.test_commit_validates_staged_content_not_worktree'),
]
for name, file, before, after, test in CASES:
    with tempfile.TemporaryDirectory(prefix='sdd-mutation-') as temp:
        target = Path(temp)
        for folder in ('scripts', '.claude', '.specs'):
            shutil.copytree(SOURCE / folder, target / folder, ignore=shutil.ignore_patterns('__pycache__'))
        path = target / file
        content = path.read_text()
        if before not in content:
            raise SystemExit(f'FAIL: mutation anchor missing: {name}')
        path.write_text(content.replace(before, after))
        result = subprocess.run(['python3', '-m', 'unittest', test], cwd=target / 'scripts/tests', env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), text=True, capture_output=True)
        detected = 'FAIL:' in result.stderr or (name == 'Stop emits text' and 'json.decoder.JSONDecodeError' in result.stderr)
        if result.returncode == 0 or not detected:
            raise SystemExit(f'FAIL: counterproof did not fail its assertion: {name}\n{result.stdout}{result.stderr}')
        print(f'OK: regression detects {name}')
