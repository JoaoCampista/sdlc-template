#!/usr/bin/env python3
"""Codex adapter: transport translation only; every policy decision belongs to the canonical guards.

`hook EVENT` reads the Codex hook payload and answers through .claude/hooks/_run.sh (so the round is logged, as
"codex"). `install` writes .codex/hooks.json once; a different existing file is preserved for human review.
Not exercised against the Codex runtime by this template's tests: check the firing in the real client.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd import ROOT  # noqa: E402

EVENTS = ('SessionStart', 'PreToolUse', 'PostToolUse', 'Stop')
STOP_HOOKS = ('stop-check.sh', 'governance-check.sh', 'role-check.sh', 'infra-check.sh')


class Refused(Exception):
    pass


def canonical(hook, payload):
    result = subprocess.run(['bash', str(ROOT / '.claude/hooks/_run.sh'), hook], input=json.dumps(payload), capture_output=True, text=True,
                            env=dict(os.environ, HARNESS_QUEM='codex', CLAUDE_PROJECT_DIR=str(ROOT)))
    if result.returncode != 0:
        raise Refused(f'guard canônico falhou: {hook}: {result.stderr.strip()[:200]}')
    return result.stdout


def patch_paths(text):
    """Validate the patch grammar before trusting any path; content prefixes are not headers."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    if not lines or lines[0] != '*** Begin Patch':
        raise Refused('início do patch inválido')
    paths, state, body, moved, ended = [], 'header', 0, False, False
    for line in lines[1:]:
        if ended:
            raise Refused('texto depois do fim do patch')
        header = next((kind for kind in ('Add', 'Update', 'Delete') if line.startswith(f'*** {kind} File: ')), None)
        if header or line == '*** End Patch':
            if state == 'update' and body == 0:
                raise Refused('atualização sem corpo')
            if line == '*** End Patch':
                if not paths:
                    raise Refused('patch sem arquivos')
                ended = True
                continue
            path = line.split(': ', 1)[1]
            if not path or path != path.strip() or path.startswith('~') or any(ord(char) < 32 or ord(char) == 127 for char in path):
                raise Refused('caminho de patch inválido')
            paths.append(path)
            state, body, moved = header.lower(), 0, False
        elif line.startswith('*** Move to: '):
            path = line.split(': ', 1)[1]
            if state != 'update' or body or moved or not path or path != path.strip() or path.startswith('~') or any(ord(char) < 32 for char in path):
                raise Refused('move fora da atualização ou destino inválido')
            paths.append(path)
            moved = True
        elif state == 'add' and line.startswith('+'):
            body += 1
        elif state == 'update' and (line == '@@' or line.startswith('@@ ')):
            pass
        elif state == 'update' and line == '*** End of File' and body:
            state = 'finished'
        elif state == 'update' and line[:1] in (' ', '+', '-'):
            body += 1
        else:
            raise Refused('gramática do patch não reconhecida')
    if not ended:
        raise Refused('patch incompleto')
    return paths


def pre_guard(hook, payload):
    """None = allowed; otherwise the deny to print. Codex has no ask: it becomes a denial, never an escape."""
    raw = canonical(hook, payload)
    if not raw.strip():
        return None
    answer = json.loads(raw)
    if answer == {}:
        return None
    specific = answer.get('hookSpecificOutput') if isinstance(answer, dict) else None
    if not isinstance(specific, dict) or specific.get('permissionDecision') not in ('deny', 'ask', 'allow') or not isinstance(specific.get('permissionDecisionReason'), str):
        raise Refused('resposta canônica inválida')
    if specific['permissionDecision'] == 'allow':
        return None
    if specific['permissionDecision'] == 'ask':
        specific = dict(specific, permissionDecision='deny', permissionDecisionReason=specific['permissionDecisionReason'] + ' — O Codex não implementa ask; operação bloqueada para decisão humana, sem conceder escape.')
    return dict(hookSpecificOutput=specific)


def hook(event):
    if event not in EVENTS:
        raise Refused('evento sem tradução')
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict) or payload.get('hook_event_name') != event or not isinstance(payload.get('cwd'), str) or not payload['cwd']:
        raise Refused('payload inválido ou evento divergente')
    if Path(payload['cwd']).resolve() != ROOT:
        raise Refused('cwd diverge da raiz do clone')
    if event == 'SessionStart':
        print(json.dumps(dict(hookSpecificOutput=dict(hookEventName='SessionStart', additionalContext=canonical('session-start.sh', payload))), ensure_ascii=False))
        return
    if event == 'Stop':
        if not isinstance(payload.get('stop_hook_active'), bool):
            raise Refused('stop_hook_active inválido')
        reasons = []
        for name in STOP_HOOKS:
            answer = json.loads(canonical(name, payload))
            if answer != {}:
                if not isinstance(answer, dict) or answer.get('decision') != 'block' or not isinstance(answer.get('reason'), str) or not answer['reason']:
                    raise Refused('resposta Stop inválida')
                reasons.append(answer['reason'])
        print(json.dumps(dict(decision='block', reason=' '.join(reasons)), ensure_ascii=False) if reasons else '{}')
        return
    tool_input = payload.get('tool_input')
    if not isinstance(payload.get('tool_name'), str) or not isinstance(tool_input, dict) or not isinstance(tool_input.get('command'), str) or not tool_input['command']:
        raise Refused('ferramenta ou comando sem tradução')
    if 'workdir' in tool_input and (not isinstance(tool_input['workdir'], str) or Path(tool_input['workdir']).resolve() != ROOT):
        raise Refused('workdir divergente; falta prova de runtime')
    tool = payload['tool_name']
    if tool == 'Bash' and event == 'PreToolUse':
        # agent_type "codex": never the main Claude session, the only one that edits the enforcement.
        denial = pre_guard('bash-guard.sh', dict(payload, agent_type='codex'))
    elif tool == 'apply_patch':
        paths = patch_paths(tool_input['command'])
        if event == 'PostToolUse':
            # The runtime does not document the patch result: never infer success nor format after a failure.
            raise Refused('pós-edição depende de prova de runtime; confira o resultado, o formato e make sdd explicitamente')
        denial = None
        for path in paths:
            denial = pre_guard('pre-edit-guard.sh', dict(cwd=str(ROOT), tool_name='Edit', tool_input=dict(file_path=path), agent_type='codex'))
            if denial:
                break
    else:
        raise Refused(f'ferramenta sem tradução comprovada: {tool}')
    print(json.dumps(denial or {}, ensure_ascii=False))


def install():
    if Path.cwd().resolve() != ROOT:
        raise Refused('rode na raiz do clone')
    folder, target = ROOT / '.codex', ROOT / '.codex/hooks.json'
    if folder.is_symlink() or target.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise Refused('.codex e hooks.json não podem ser symlink nem outro tipo de arquivo')
    command = lambda event: dict(type='command', command=f"bash {shlex.quote(str(ROOT / 'scripts/sdd/codex-hook.sh'))} {event}")  # noqa: E731
    wanted = dict(hooks=dict(SessionStart=[dict(hooks=[command('SessionStart')])],
                             PreToolUse=[dict(matcher='^(Bash|apply_patch)$', hooks=[command('PreToolUse')])],
                             PostToolUse=[dict(matcher='apply_patch', hooks=[command('PostToolUse')])],
                             Stop=[dict(hooks=[command('Stop')])]))
    if target.exists():
        if json.loads(target.read_text()) != wanted:
            raise Refused('hooks.json diferente; revisão humana necessária, arquivo preservado')
        print('codex-hooks: configuração equivalente preservada')
        return
    folder.mkdir(exist_ok=True)
    with open(target, 'x', encoding='utf-8') as handle:  # never overwrites a file that appeared meanwhile
        handle.write(json.dumps(wanted, indent=2) + '\n')
    print('codex-hooks: configuração criada; abra a sessão na raiz do clone e revise a confiança dos hooks no cliente')


if __name__ == '__main__':
    try:
        if sys.argv[1:2] == ['hook'] and len(sys.argv) == 3:
            hook(sys.argv[2])
        elif sys.argv[1:] == ['install']:
            install()
        else:
            raise Refused('uso: codex.py hook EVENTO | install')
    except (Refused, ValueError, OSError, KeyError, TypeError) as exc:
        print(f'codex-hook: {exc}', file=sys.stderr)
        sys.exit(2)
