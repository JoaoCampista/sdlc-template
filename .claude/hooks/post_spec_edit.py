#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
from guard import ROOT, classify
try:
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict) or not isinstance(payload.get('tool_input'), dict): raise ValueError('entrada inválida')
    cwd = Path(payload.get('cwd', str(ROOT))).resolve()
    raw = payload['tool_input']['file_path']
    _, path = classify(raw, cwd)
    if path.is_relative_to(ROOT / '.specs') and path.suffix == '.md':
        for script, args in [('spec-lint.sh', [str(path)]), ('spec-index.sh', [])]:
            result = subprocess.run(['bash', str(ROOT / 'scripts/sdd' / script), *args], cwd=ROOT, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT)), capture_output=True, text=True)
            if result.returncode:
                print(result.stdout + result.stderr, file=sys.stderr)
                sys.exit(2)
    print('{}')
except (ValueError, OSError, KeyError, TypeError) as exc:
    print(f'PostToolUse: {exc}', file=sys.stderr)
    sys.exit(2)
