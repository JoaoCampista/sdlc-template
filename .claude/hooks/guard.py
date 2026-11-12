#!/usr/bin/env python3
"""Conservative workflow guard, not a shell sandbox. See docs/hooks.md."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/sdd'))
from sdd import ROOT, code_reason
import harness

LONG_RUN = ('Rodada longa com a saída num pipe sem tee esconde o progresso: grave a saída inteira num arquivo, '
            'CMD > ARQ.log 2>&1 (em segundo plano) ou CMD 2>&1 | tee ARQ.log | grep …; o status se conta a qualquer hora no arquivo.')


def decision(action, reason, hold=False):
    """hold marks what stays with the human: in the development stage it is denied instead of asked."""
    return dict(hookSpecificOutput=dict(hookEventName='PreToolUse', permissionDecision=action, permissionDecisionReason=reason), hold=hold)


def action_of(result):
    return result['hookSpecificOutput']['permissionDecision'] if result else None


def stronger(pending, result):
    """Keep the ask that stays with the human over one that the development stage lets through."""
    if result is None or (pending is not None and pending.get('hold') and not result.get('hold')):
        return pending
    return result


def classify(raw, cwd):
    if not isinstance(raw, str) or not raw or any(ord(char) < 32 for char in raw):
        raise ValueError('caminho ausente ou inválido')
    path = Path(raw).expanduser()
    path = (cwd / path).resolve() if not path.is_absolute() else path.resolve()
    # Python versions differ on non-strict resolve of cycles: unresolved links are never an allow.
    if any(candidate.is_symlink() for candidate in (path, *path.parents)):
        raise ValueError('symlink não resolvido ou cíclico')
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        # An edit in a sibling worktree must use its own session/state, not borrow this spec.
        existing = path if path.is_dir() else path.parent
        while not existing.exists(): existing = existing.parent
        def common(root):
            result = subprocess.run(['git', '-C', str(root), 'rev-parse', '--path-format=absolute', '--git-common-dir'], capture_output=True, text=True)
            return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None
        own = common(ROOT)
        if own is not None and common(existing) == own:
            return 'other-worktree', path
        return 'outside', path
    low = rel.lower()
    if low == '.specs/index.json': return 'generated', path
    if low == '.git' or low.startswith('.git/'): return 'git', path
    if low == '.claude/deploy-stage.json': return 'stage', path
    if (low.startswith(('.claude/hooks/', 'scripts/sdd/', '.github/', '.codex/')) or low in ('.claude/hooks', 'scripts/sdd', '.github', '.codex')
            or low in ('.claude/harness.json', '.claude/agents/spec-reviewer.md') or re.match(r'^\.claude/settings[^/]*\.json$', low)):
        return 'harness', path
    if low.startswith(('.specs/', '.sdd/', 'docs/')) or low.endswith('.md') or low == '.gitignore':
        return 'free', path
    return 'code', path


def edit_path(raw, cwd, agent='', shell=False):
    kind, path = classify(raw, cwd)
    if kind in ('generated', 'git'):
        return decision('deny', 'Arquivo gerado/controlado: use scripts/sdd/spec-index.sh ou os comandos Git apropriados.')
    if kind == 'other-worktree':
        return decision('deny', 'Use a sessão e a spec ativa da worktree de destino.')
    if kind in ('harness', 'stage'):
        if agent:
            return decision('deny', 'Enforcement do método: só a sessão principal o edita, nunca um subagente nem outro cliente (AGENTS.md, Regra 10). Devolva a mudança no relatório.')
        if kind == 'stage':
            return decision('ask', 'Trocar o estágio muda o que o guard pergunta: é decisão do humano (AGENTS.md, Regra 9).', hold=True)
        if shell:
            return decision('ask', 'Enforcement só pela ferramenta Edit/Write da sessão principal, nunca pelo shell (AGENTS.md, Regra 9).', hold=True)
        if harness.stage() != 'desenvolvimento':
            return decision('ask', 'Mudança no enforcement: confira escopo autorizado, diff e testes de regressão; a permissão do runtime pode exigir confirmação.')
        return None
    if kind == 'code':
        reason = code_reason()
        if reason: return decision('deny', reason)
    return None


def long_runs():
    try:
        return set(harness.config()['long_runs'])
    except ValueError:
        return set(harness.DEFAULTS['long_runs'])


def bash_guard(command, cwd, depth=0, agent=''):
    if not isinstance(command, str) or not command.strip(): raise ValueError('comando ausente')
    if depth > 4: return decision('ask', 'Comando aninhado: revisar manualmente.')
    if '#' in command and '\n' in command:
        return decision('ask', 'Comentários em comando multilinha: revisar limites e efeitos; shlex não preserva essa estrutura.')
    # shlex does not evaluate variables, substitutions, heredocs or shell programs.
    if any(marker in command for marker in ('$(', '`', '<<', '${', '<(', '>(')):
        return decision('ask', 'Expansão, heredoc ou substituição: o guard não interpreta; revisar o comando e seus efeitos.')
    lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|<>\n')
    lexer.whitespace = ' \t\r'  # preserve command boundaries on newlines
    tokens = list(lexer)
    pieces, part = [], []  # each piece: (words, the separator that follows it)
    for token in tokens:
        if token and set(token) <= set(';&|\n'):
            if part: pieces.append((part, token)); part = []
        else: part.append(token)
    if part: pieces.append((part, ''))
    pending = None
    long_targets = long_runs()
    for index, (words, separator) in enumerate(pieces):
        # Deal with redirections before dropping assignment prefixes.
        for i, token in enumerate(words):
            if token in ('>', '>>', '>|', '>&', '&>', '&>>') and i + 1 < len(words):
                if words[i + 1].isdigit() or words[i + 1] in ('/dev/null', '/dev/stderr', '/dev/stdout'): continue
                result = edit_path(words[i + 1], cwd, agent, shell=True)
                if action_of(result) == 'deny': return result
                pending = stronger(pending, result)
        if any(re.match(r'(?:SDD_ALLOW_TRIVIAL|CLAUDE_PROJECT_DIR)=', word) for word in words):
            return decision('deny', 'O agente não redefine escapes ou a raiz usada pelos guards.')
        while words and re.match(r'^\w+=', words[0]): words = words[1:]
        if not words: continue
        executable = Path(words[0]).name
        args = words[1:]
        if executable == 'cd':
            if len(args) != 1 or '$' in args[0]: return decision('ask', 'cd dinâmico: revisar destino.')
            cwd = (cwd / Path(args[0]).expanduser()).resolve()
            continue
        if executable in ('make', 'gmake') and separator in ('|', '|&') and any(arg in long_targets for arg in args):
            # The whole output goes to a file only when the very next command is tee with a file argument.
            following = pieces[index + 1][0] if index + 1 < len(pieces) else []
            operands = []
            for arg in following[1:]:
                if arg in ('>', '>>', '>&', '&>', '<'): break
                if not arg.startswith('-') and not arg.isdigit(): operands.append(arg)
            if not (following and Path(following[0]).name == 'tee' and operands):
                return decision('deny', LONG_RUN)
        if executable in ('env', 'command', 'nice', 'sudo', 'xargs', 'eval', 'exec', 'source', '.'):
            return decision('ask', 'Wrapper ou execução indireta: revisar comando efetivo; não usar para contornar guards.')
        if executable in ('bash', 'sh', 'zsh') and '-c' in args:
            pos = args.index('-c')
            if pos + 1 >= len(args): raise ValueError('shell -c sem programa')
            result = bash_guard(args[pos + 1], cwd, depth + 1, agent)
            if action_of(result) == 'deny': return result
            pending = stronger(pending, result)
        elif executable in ('python', 'python3', 'ruby', 'node', 'perl', 'bash', 'sh', 'zsh'):
            trusted = args and (args[0] in ('scripts/setup.sh', 'scripts/doctor.sh') or re.fullmatch(r'scripts/sdd/[A-Za-z0-9-]+\.sh', args[0])) and cwd == ROOT
            if not trusted: pending = stronger(pending, decision('ask', 'Programa opaco ao guard: revisar script e destinos antes de executar.'))
        if executable == 'git':
            joined = ' '.join(args)
            if 'core.hooksPath' in joined or any(a.startswith('--no-ver') for a in args) or ('commit' in args and '-n' in args):
                return decision('deny', 'Não contorne os hooks Git.')
            if 'add' in args and any(a in ('-A', '--all', '.', ':/', '-u', '-f', '--force') for a in args):
                return decision('deny', 'Stage por caminhos explícitos, sem -f/-A/--all/-u; confira o índice antes do commit.')
            if ('reset' in args and '--hard' in args) or 'clean' in args or ('push' in args and any(a.startswith('--force') or a == '-f' for a in args)):
                return decision('ask', 'Operação Git destrutiva: requer escopo explícito autorizado pelo humano.', hold=True)
            if any(a in ('apply', 'checkout', 'restore', 'rebase', 'merge') for a in args):
                pending = stronger(pending, decision('ask', 'Operação altera a árvore: conferir spec, arquivos locais e autorização.'))
        if executable in ('docker', 'podman') and any(a in ('--volumes', '-v', 'prune') for a in args):
            return decision('ask', 'Remoção de volumes ou dados de contêiner: confirme o alvo e a autorização existente.', hold=True)
        if executable in ('rm', 'rmdir'):
            pending = stronger(pending, decision('ask', 'Remoção potencialmente destrutiva: confirme o alvo e a autorização existente.'))
        if executable in ('psql', 'mysql', 'redis-cli', 'docker', 'podman') and re.search(r'\b(DROP|TRUNCATE|DELETE\s+FROM|FLUSHALL|FLUSHDB)\b', command, re.I):
            return decision('ask', 'Operação sobre dados: revisar destino real e autorização antes de executar.', hold=True)
        paths = []
        plain = [a for a in args if not a.startswith('-')]
        if executable in ('touch', 'mkdir', 'tee', 'rm', 'rmdir'): paths = plain
        elif executable in ('cp', 'install', 'ln', 'rsync') and plain: paths = plain[-1:]
        elif executable == 'mv': paths = plain
        elif executable == 'sed' and any(a.startswith('-i') for a in args): paths = plain[-1:]
        elif executable == 'dd': paths = [a[3:] for a in args if a.startswith('of=')]
        elif executable in ('curl', 'sort'):
            for i, arg in enumerate(args[:-1]):
                if arg in ('-o', '--output'): paths.append(args[i + 1])
        for path in paths:
            if '$' in path or '*' in path or '?' in path:
                pending = stronger(pending, decision('ask', 'Destino dinâmico: revisar caminho efetivo.'))
                continue
            result = edit_path(path, cwd, agent, shell=True)
            if action_of(result) == 'deny': return result
            pending = stronger(pending, result)
    return pending


def by_stage(result, command, cwd, agent):
    """Outside development every ask reaches the human. In development nothing waits for the human: what stays with
    them is denied with the reason, and the rest passes and leaves a line in .sdd/auto-aprovado.log."""
    if action_of(result) != 'ask' or harness.stage() != 'desenvolvimento':
        return result
    reason = result['hookSpecificOutput']['permissionDecisionReason']
    if result.get('hold'):
        return decision('deny', reason + ' No estágio de desenvolvimento o guard não pergunta: siga sem este passo e deixe o pedido ao humano no relatório.')
    try:
        if harness.STATE.is_dir():
            with open(harness.AUTO_LOG, 'a', encoding='utf-8') as handle:
                handle.write('\t'.join([harness.stamp(), agent or 'principal', str(cwd), harness.mask(command), harness.mask(reason)]) + '\n')
    except OSError:
        pass
    return None


def main():
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict) or not isinstance(payload.get('tool_input'), dict): raise ValueError('entrada inválida')
    cwd = Path(payload.get('cwd', str(ROOT))).resolve()
    # A subagent (or another client translated by an adapter) carries agent_id or agent_type; each field on its own.
    agent = next((str(payload[key]) for key in ('agent_id', 'agent_type') if payload.get(key) not in (None, '')), '')
    mode = sys.argv[1]
    if mode == 'bash':
        command = payload['tool_input'].get('command')
        result = by_stage(bash_guard(command, cwd, agent=agent), command, cwd, agent)
    else:
        key = 'notebook_path' if payload.get('tool_name') == 'NotebookEdit' else 'file_path'
        result = edit_path(payload['tool_input'].get(key), cwd, agent)
    if result: result = dict(hookSpecificOutput=result['hookSpecificOutput'])
    print(json.dumps(result or {}))


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f'Guard SDD: entrada/estado inválido; ferramenta bloqueada: {exc}', file=sys.stderr)
        sys.exit(2)
