#!/usr/bin/env python3
"""Stop checks that keep records in step with the work, the role mark, and the guards around subagents.

Stop hooks print exactly one JSON object; diagnostics go to stderr. An internal error never allows: exit 2.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/sdd'))
from sdd import ROOT  # noqa: E402
import harness  # noqa: E402
import sync  # noqa: E402

STATE = ROOT / '.sdd'
ERRORS = (ValueError, OSError, subprocess.CalledProcessError)


def deny(reason):
    print(json.dumps(dict(hookSpecificOutput=dict(hookEventName='PreToolUse', permissionDecision='deny', permissionDecisionReason=reason))))


def caller(payload):
    """Non-empty for a subagent: each field on its own, so an empty agent_id never masks a valid agent_type."""
    return next((str(payload[key]) for key in ('agent_id', 'agent_type') if payload.get(key) not in (None, '')), '')


def answer(payload, problems):
    """Block once with the reason; on the second stop in a row only inform, so the agent is never held in a loop."""
    active = payload.get('stop_hook_active', False)
    if not isinstance(active, bool):
        raise ValueError('stop_hook_active deve ser booleano')
    if problems and not active:
        print(json.dumps(dict(decision='block', reason=' '.join(problems)), ensure_ascii=False))
        return
    if problems:
        print('Stop (já avisado nesta parada): ' + ' '.join(problems), file=sys.stderr)
    print('{}')


def stop_governance(payload):
    tip = sync.head()
    if not tip:
        return answer(payload, [])
    todo = 'atualize o product-spec (subagente produto), a Constitution (com o G2 do humano) ou trate a clarificação, ou registre "conferido, nada a mudar" com bash scripts/sdd/governance-sync.sh ack MOTIVO'
    mark_file = STATE / 'governance-head'
    mark = sync.read_mark(mark_file)
    if mark is None:
        return answer(payload, [f'GOVERNANÇA SEM REGISTRO: não há .sdd/governance-head — {todo}.'])
    if not sync.valid_mark(mark, tip):
        return answer(payload, [f'GOVERNANÇA COM REGISTRO INVÁLIDO: .sdd/governance-head não é um commit do histórico do HEAD — {todo}.'])
    try:
        findings = sync.governance_check(mark)
    except ERRORS as exc:
        return answer(payload, [f'GOVERNANÇA NÃO CONFERIDA: {exc} — {todo}.'])
    if findings:
        return answer(payload, [f"DOCUMENTOS DE CIMA ATRASADOS: {len(findings)} achado(s) desde {mark[:8]} ({'; '.join(findings[:6])}) — {todo}."])
    try:
        mark_file.write_text(tip + '\n')  # nothing pending up to here: the mark advances
    except OSError:
        pass
    answer(payload, [])


def stop_roles(payload):
    if not sync.head():
        return answer(payload, [])
    try:
        findings = sync.role_findings()
    except ERRORS as exc:
        findings = [f'PAPÉIS NÃO CONFERIDOS: {exc} — corrija .claude/harness.json ou o repositório Git.']
    answer(payload, findings)


def stop_infra(payload):
    if not sync.head():
        return answer(payload, [])
    todo = 'rode o plano e o apply da raiz, ou registre "conferido, nada a aplicar" com bash scripts/sdd/infra-sync.sh ack RAIZ MOTIVO'
    try:
        findings = sync.infra_check()
    except ERRORS as exc:
        return answer(payload, [f'INFRA NÃO CONFERIDA: {exc} — {todo}.'])
    seen = STATE / 'infra-check-seen'
    if not findings:
        try:
            seen.unlink()
        except OSError:
            pass
        return answer(payload, [])
    text = '\n'.join(findings)
    # The same findings already blocked once: only the human clears them (a login, an apply), so blocking every turn
    # again loops without news. New findings block again.
    try:
        repeated = seen.read_text() == text
    except OSError:
        repeated = False
    if repeated:
        payload = dict(payload, stop_hook_active=True)
    elif not payload.get('stop_hook_active', False):
        try:
            STATE.mkdir(exist_ok=True)
            seen.write_text(text)
        except OSError:
            print('Stop (infra): não gravei .sdd/infra-check-seen; a próxima parada bloqueia de novo', file=sys.stderr)
    answer(payload, [f"INFRA COMMITADA SEM APPLY: {'; '.join(findings[:4])} — {todo}."])


def role_mark(payload):
    """Pre/PostToolUse of Agent, Task and SendMessage. Never blocks and never decides.

    The hooks of one event run in parallel, so the PreToolUse cannot know whether another guard denied the call: it
    keeps the HEAD of the request per tool_use_id, and only the PostToolUse (which runs when the tool ran) turns it
    into the mark. Only the main session moves marks.
    """
    try:
        if caller(payload):
            return
        roles = harness.config()['roles']
        tool, tool_input = payload.get('tool_name'), payload.get('tool_input') if isinstance(payload.get('tool_input'), dict) else {}
        call = str(payload.get('tool_use_id') or '')
        post = payload.get('hook_event_name') == 'PostToolUse'
        if not re.fullmatch(r'[A-Za-z0-9_-]+', call):
            return
        role = None
        if tool in ('Agent', 'Task') and tool_input.get('subagent_type') in roles:
            role = tool_input['subagent_type']
        elif tool == 'SendMessage' and re.fullmatch(r'[0-9a-f]+', str(tool_input.get('to') or '')):
            for name in roles:  # a role agent that is being continued
                try:
                    known = sync.role_file(name, 'ids').read_text().split()
                except OSError:
                    known = []
                if tool_input['to'] in known:
                    role = name
        if role is None:
            return
        pending = sync.role_file(role, 'pending') / call
        if not post:
            tip = sync.head()
            if tip:
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(tip + '\n')
            return
        if pending.is_file() and pending.stat().st_size:
            pending.replace(sync.role_file(role, 'head'))
        if tool in ('Agent', 'Task'):
            found = re.search(r'agent_?[iI]d"?:? *"?([0-9a-f]{8,})', json.dumps(payload.get('tool_response')))
            if found:
                with open(sync.role_file(role, 'ids'), 'a') as handle:
                    handle.write(found.group(1) + '\n')
    except ERRORS + (TypeError, KeyError):
        pass  # a mark that was not written only leaves the old one, and the Stop asks again


def message_guard(payload):
    if caller(payload) and str((payload.get('tool_input') or {}).get('to', '')) != 'main':
        return deny('Subagente só manda mensagem à sessão principal: use "to": "main". Outra sessão, o auditor, o humano e outro subagente ficam fora (AGENTS.md, Regra 10, "O time"); o que for para eles vai no relatório final ou numa mensagem à sessão principal, que repassa.')
    print('{}')


def inside_repo(path):
    if path == ROOT or ROOT in path.parents:
        return True
    for candidate in (path, *path.parents):
        try:
            if candidate.exists() and os.path.samefile(candidate, ROOT):
                return True  # another name of the same folder (case-insensitive volume, alias)
        except OSError:
            return True
    return False


def reviewer_guard(payload, mode):
    """The reviewer only reads: Edit/Write pass only in its memory (.md) and in the mutation copy outside the repository."""
    agent = str(payload.get('agent_type') or '')
    if mode == 'settings':
        if agent != 'spec-reviewer':
            return print('{}')  # outside the reviewer the pre-edit guard decides
    elif mode != '':
        raise ValueError(f'modo desconhecido: {mode}')
    memory = ROOT / '.claude/agent-memory-local/spec-reviewer'

    def refuse(reason):
        deny(f'O spec-reviewer só lê (AGENTS.md, Regra 10): {reason} Escreva só na sua memória ({memory}/, arquivo .md) ou na cópia de mutação, em SCRATCHPAD/spec-reviewer/. O conserto vai no relatório.')

    key = {'Edit': 'file_path', 'Write': 'file_path', 'MultiEdit': 'file_path', 'NotebookEdit': 'notebook_path'}.get(payload.get('tool_name'))
    if key is None:
        return refuse(f"a ferramenta {payload.get('tool_name')!r} não é das quatro que este guard conhece.")
    raw = (payload.get('tool_input') or {}).get(key)

    def clean(value, label):
        if not isinstance(value, str) or not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
            return f'{label} vazio, que não é texto ou com caractere de controle.'
        if not value.startswith('/'):
            return f'{label} relativo ({value}): use o absoluto.'
        if any(part in ('.', '..') for part in value.split('/')):
            return f'{label} com "." ou ".." ({value}): com symlink no meio, o texto e o disco resolvem diferente.'
        return ''

    problem = clean(raw, 'caminho')
    if problem:
        return refuse(problem)
    real = Path(os.path.realpath(raw))
    if any(candidate.is_symlink() for candidate in (real, *real.parents)):
        return refuse(f'o caminho passa por um symlink que não se resolve ({raw}).')

    def single_link():
        # A hard link writes to the same inode, which may be a repository file, and no path shows it.
        if real.is_file() and real.stat().st_nlink > 1:
            refuse(f'o arquivo tem outro nome no disco (link físico): {real}.')
            return False
        return True

    if memory in real.parents:  # the literal folder: a symlink in its place takes the real path out of the prefix
        if real.suffix.lower() != '.md':
            return refuse(f'na memória só vale arquivo .md ({raw}).')
        return print('{}') if single_link() else None
    scratch = payload.get('scratchpad_dir')
    if scratch:
        problem = clean(scratch, 'scratchpad_dir')
        if problem:
            return refuse(problem)
        zone = Path(os.path.realpath(scratch)) / 'spec-reviewer'
        if zone in real.parents:
            if inside_repo(real):
                return refuse(f'a cópia de mutação cai dentro do repositório ({raw}).')
            return print('{}') if single_link() else None
    refuse(f'{raw} fica fora da sua memória e da cópia de mutação.')


def main():
    mode, *args = sys.argv[1:]
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError('entrada deve ser objeto JSON')
    if mode == 'stop-governance':
        stop_governance(payload)
    elif mode == 'stop-roles':
        stop_roles(payload)
    elif mode == 'stop-infra':
        stop_infra(payload)
    elif mode == 'role-mark':
        role_mark(payload)
    elif mode == 'message-guard':
        message_guard(payload)
    elif mode == 'reviewer-guard':
        reviewer_guard(payload, args[0] if args else '')
    else:
        raise ValueError('modo desconhecido')


if __name__ == '__main__':
    try:
        main()
    except ERRORS + (TypeError, KeyError, IndexError) as exc:
        if sys.argv[1:2] == ['role-mark']:
            sys.exit(0)  # the mark never blocks a tool
        print(f'Hook SDD: entrada/estado inválido; bloqueado: {exc}', file=sys.stderr)
        sys.exit(2)
