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
    ('runner does not log', 'scripts/sdd/harness.py', "        record(name, data.decode", "        (lambda *a: None)(name, data.decode", 'test_harness.Harness.test_runner_same_answer_logs_round_and_fails_closed'),
    ('stage never denies', '.claude/hooks/guard.py', "    if result.get('hold'):", "    if False:", 'test_harness.Harness.test_stage_decides_what_asked_the_human'),
    ('subagent edits enforcement', '.claude/hooks/guard.py', "        if agent:\n            return decision('deny', 'Enforcement", "        if False:\n            return decision('deny', 'Enforcement", 'test_team.Team.test_subagent_cannot_edit_enforcement_or_message_others'),
    ('long run in a pipe', '.claude/hooks/guard.py', "                return decision('deny', LONG_RUN)", "                pass", 'test_harness.Harness.test_long_run_in_a_pipe_needs_tee'),
    ('governance finding advances mark', '.claude/hooks/team.py', "    if findings:\n        return answer(payload, [f\"DOCUMENTOS", "    if False:\n        return answer(payload, [f\"DOCUMENTOS", 'test_team.Team.test_governance_blocks_stale_upper_documents'),
    ('role mark on request', '.claude/hooks/team.py', "        if not post:\n            tip = sync.head()\n            if tip:\n                pending.parent.mkdir(parents=True, exist_ok=True)\n                pending.write_text(tip + '\\n')\n            return", "        if not post:\n            tip = sync.head()\n            if tip:\n                sync.role_file(role, 'head').parent.mkdir(parents=True, exist_ok=True)\n                sync.role_file(role, 'head').write_text(tip + '\\n')\n            return", 'test_team.Team.test_role_paths_block_until_the_role_agent_ran'),
    ('reviewer hard link', '.claude/hooks/team.py', "        if real.is_file() and real.stat().st_nlink > 1:", "        if False:", 'test_team.Team.test_reviewer_writes_only_memory_and_mutation_copy'),
    ('message guard', '.claude/hooks/team.py', "    if caller(payload) and str(", "    if False and str(", 'test_team.Team.test_subagent_cannot_edit_enforcement_or_message_others'),
    ('task sync', 'scripts/sdd/sync.py', "            if tasks not in touched:", "            if False:", 'test_team.Team.test_code_that_cites_a_task_goes_up_with_tasks_md'),
    ('opaque construct hides a hold', '.claude/hooks/guard.py', "    return decision('ask', reason + (' O texto cita operação destrutiva, enforcement ou escrita sem spec ativa.' if hold else ''), hold=hold)", "    return decision('ask', reason)", 'test_harness.Harness.test_stage_decides_what_asked_the_human'),
    ('state files are free', '.claude/hooks/guard.py', "    if kind == 'state':", "    if False:", 'test_harness.Harness.test_stage_decides_what_asked_the_human'),
    ('unreadable git is green', 'scripts/sdd/sync.py', "    raise ValueError('o Git não leu o HEAD deste repositório')", "    return ''", 'test_team.Team.test_role_paths_block_until_the_role_agent_ran'),
    ('codex ask stays ask', 'scripts/sdd/codex.py', "    if specific['permissionDecision'] == 'ask':", "    if False:", 'test_harness.Harness.test_codex_adapter_translates_and_refuses'),
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
