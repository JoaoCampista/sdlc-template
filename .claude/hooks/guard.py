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


def decision(action, reason):
    return dict(hookSpecificOutput=dict(hookEventName='PreToolUse', permissionDecision=action, permissionDecisionReason=reason))


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
    if (low.startswith(('.claude/hooks/', 'scripts/sdd/', '.github/')) or low in ('.claude/hooks', 'scripts/sdd', '.github')
            or re.match(r'^\.claude/settings[^/]*\.json$', low)):
        return 'harness', path
    if low.startswith(('.specs/', '.sdd/', 'docs/')) or low.endswith('.md') or low == '.gitignore':
        return 'free', path
    return 'code', path


def edit_path(raw, cwd):
    kind, path = classify(raw, cwd)
    if kind in ('generated', 'git'):
        return decision('deny', 'Arquivo gerado/controlado: use scripts/sdd/spec-index.sh ou os comandos Git apropriados.')
    if kind == 'other-worktree':
        return decision('deny', 'Use a sessão e a spec ativa da worktree de destino.')
    if kind == 'harness':
        return decision('ask', 'Mudança no enforcement: confira escopo autorizado, diff e testes de regressão; a permissão do runtime pode exigir confirmação.')
    if kind == 'code':
        reason = code_reason()
        if reason: return decision('deny', reason)
    return None


def bash_guard(command, cwd, depth=0):
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
    pieces, part = [], []
    for token in tokens:
        if token and set(token) <= set(';&|\n'):
            if part: pieces.append(part); part = []
        else: part.append(token)
    if part: pieces.append(part)
    pending = None
    for words in pieces:
        # Deal with redirections before dropping assignment prefixes.
        for i, token in enumerate(words):
            if token in ('>', '>>', '>|', '>&', '&>', '&>>') and i + 1 < len(words):
                if words[i + 1].isdigit() or words[i + 1] in ('/dev/null', '/dev/stderr', '/dev/stdout'): continue
                result = edit_path(words[i + 1], cwd)
                if result:
                    if result['hookSpecificOutput']['permissionDecision'] == 'deny': return result
                    pending = result
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
        if executable in ('env', 'command', 'nice', 'sudo', 'xargs', 'eval', 'exec', 'source', '.'):
            return decision('ask', 'Wrapper ou execução indireta: revisar comando efetivo; não usar para contornar guards.')
        if executable in ('bash', 'sh', 'zsh') and '-c' in args:
            pos = args.index('-c')
            if pos + 1 >= len(args): raise ValueError('shell -c sem programa')
            result = bash_guard(args[pos + 1], cwd, depth + 1)
            if result:
                if result['hookSpecificOutput']['permissionDecision'] == 'deny': return result
                pending = result
        elif executable in ('python', 'python3', 'ruby', 'node', 'perl', 'bash', 'sh', 'zsh'):
            trusted = args and args[0] in ('scripts/setup.sh', 'scripts/doctor.sh', 'scripts/sdd/spec-index.sh', 'scripts/sdd/spec-drift.sh', 'scripts/sdd/spec-lint.sh', 'scripts/sdd/spec-lint-all.sh') and cwd == ROOT
            if not trusted: pending = decision('ask', 'Programa opaco ao guard: revisar script e destinos antes de executar.')
        if executable == 'git':
            joined = ' '.join(args)
            if 'core.hooksPath' in joined or any(a.startswith('--no-ver') for a in args) or ('commit' in args and '-n' in args):
                return decision('deny', 'Não contorne os hooks Git.')
            if 'add' in args and any(a in ('-A', '--all', '.', ':/', '-u', '-f', '--force') for a in args):
                return decision('deny', 'Stage por caminhos explícitos, sem -f/-A/--all/-u; confira o índice antes do commit.')
            if ('reset' in args and '--hard' in args) or 'clean' in args or ('push' in args and any(a.startswith('--force') or a == '-f' for a in args)):
                return decision('ask', 'Operação Git destrutiva: requer escopo explícito autorizado pelo humano.')
            if any(a in ('apply', 'checkout', 'restore', 'rebase', 'merge') for a in args):
                pending = decision('ask', 'Operação altera a árvore: conferir spec, arquivos locais e autorização.')
        if executable in ('rm', 'rmdir') or (executable in ('docker', 'podman') and any(a in ('--volumes', '-v', 'prune') for a in args)):
            return decision('ask', 'Remoção potencialmente destrutiva: confirme o alvo e a autorização existente.')
        if executable in ('psql', 'mysql', 'redis-cli', 'docker', 'podman') and re.search(r'\b(DROP|TRUNCATE|DELETE\s+FROM|FLUSHALL|FLUSHDB)\b', command, re.I):
            return decision('ask', 'Operação sobre dados: revisar destino real e autorização antes de executar.')
        paths = []
        plain = [a for a in args if not a.startswith('-')]
        if executable in ('touch', 'mkdir', 'tee'): paths = plain
        elif executable in ('cp', 'install', 'ln', 'rsync') and plain: paths = plain[-1:]
        elif executable == 'mv': paths = plain
        elif executable == 'sed' and any(a.startswith('-i') for a in args): paths = plain[-1:]
        elif executable == 'dd': paths = [a[3:] for a in args if a.startswith('of=')]
        elif executable in ('curl', 'sort'):
            for i, arg in enumerate(args[:-1]):
                if arg in ('-o', '--output'): paths.append(args[i + 1])
        for path in paths:
            if '$' in path or '*' in path or '?' in path:
                pending = decision('ask', 'Destino dinâmico: revisar caminho efetivo.')
                continue
            result = edit_path(path, cwd)
            if result:
                if result['hookSpecificOutput']['permissionDecision'] == 'deny': return result
                pending = result
    return pending


def main():
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict) or not isinstance(payload.get('tool_input'), dict): raise ValueError('entrada inválida')
    cwd = Path(payload.get('cwd', str(ROOT))).resolve()
    mode = sys.argv[1]
    if mode == 'bash': result = bash_guard(payload['tool_input'].get('command'), cwd)
    else:
        key = 'notebook_path' if payload.get('tool_name') == 'NotebookEdit' else 'file_path'
        result = edit_path(payload['tool_input'].get(key), cwd)
    print(json.dumps(result or {}))


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f'Guard SDD: entrada/estado inválido; ferramenta bloqueada: {exc}', file=sys.stderr)
        sys.exit(2)
