#!/usr/bin/env python3
"""Harness plumbing: hook runner with one log line per round, report, check verdict, stage and junction check.

Standard library only. The log is measurement: failing to write it never changes a hook's answer or exit code.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd import ROOT  # noqa: E402

HOOKS = ROOT / '.claude/hooks'
STATE = ROOT / '.sdd'
AUTO_LOG = STATE / 'auto-aprovado.log'
DEFAULTS = dict(roles={}, infra_roots=[], fences=[], long_runs=['check', 'test', 'test-integration', 'test-mutations'])
INTERVENTIONS = ('deny', 'ask', 'block', 'rc2', 'recusa', 'falha', 'aponta')


def config():
    """What belongs to the project (.claude/harness.json). Absent file = defaults; invalid file raises ValueError."""
    path = ROOT / '.claude/harness.json'
    merged = {key: value for key, value in DEFAULTS.items()}
    if not path.exists():
        return merged
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError('.claude/harness.json deve ser um objeto JSON')
    merged.update(data)
    roles = merged['roles']
    if not isinstance(roles, dict):
        raise ValueError('harness.json: roles deve ser um objeto')
    for name, role in roles.items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name):
            raise ValueError(f'harness.json: nome de papel inválido: {name}')
        if not isinstance(role, dict) or not isinstance(role.get('paths', []), list) or not all(isinstance(p, str) and p for p in role.get('paths', [])):
            raise ValueError(f'harness.json: papel {name} exige paths como lista de textos')
    for key in ('infra_roots', 'fences'):
        if not isinstance(merged[key], list) or not all(isinstance(item, dict) for item in merged[key]):
            raise ValueError(f'harness.json: {key} deve ser lista de objetos')
    for root in merged['infra_roots']:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', str(root.get('name', ''))) or not isinstance(root.get('dir'), str) or not root['dir']:
            raise ValueError('harness.json: cada raiz de infra exige name e dir')
    for fence in merged['fences']:
        if not isinstance(fence.get('name'), str) or not isinstance(fence.get('run'), list) or not fence['run'] or not isinstance(fence.get('paths'), list):
            raise ValueError('harness.json: cada trava exige name, run (lista) e paths (lista)')
    if not isinstance(merged['long_runs'], list) or not all(isinstance(item, str) for item in merged['long_runs']):
        raise ValueError('harness.json: long_runs deve ser lista de textos')
    return merged


def stage():
    """'desenvolvimento' only with {"stage": "desenvolvimento"}; absent, invalid or any other value is 'beta' (asks)."""
    try:
        data = json.loads((ROOT / '.claude/deploy-stage.json').read_text())
        if isinstance(data, dict) and data.get('stage') == 'desenvolvimento':
            return 'desenvolvimento'
    except (OSError, ValueError):
        pass
    return 'beta'


def mask(text):
    text = re.sub(r'[0-9]{12}', 'CONTA', str(text))
    text = re.sub(r'[A-Za-z0-9+_=-]{32,}', 'SEGREDO?', text)
    return re.sub(r'[\n\t\r]+', ' ', text)[:300]


def now():
    return datetime.now(timezone.utc)


def stamp(moment=None):
    return (moment or now()).strftime('%Y-%m-%dT%H:%M:%SZ')


def log(entry):
    """Append one JSON line to .sdd/harness/YYYY-MM.jsonl; silent when .sdd does not exist or cannot be written."""
    try:
        if not STATE.is_dir():
            return
        folder = STATE / 'harness'
        folder.mkdir(exist_ok=True)
        with open(folder / (now().strftime('%Y-%m') + '.jsonl'), 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except OSError:
        pass


def line_count(path):
    try:
        with open(path, 'rb') as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def as_object(raw):
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def record(name, data, out, err, code, elapsed, auto):
    payload, answer = as_object(data), as_object(out)
    specific = answer.get('hookSpecificOutput') if isinstance(answer.get('hookSpecificOutput'), dict) else {}
    permission, context = specific.get('permissionDecision'), specific.get('additionalContext')
    event = payload.get('hook_event_name')
    tool_input = payload.get('tool_input') if isinstance(payload.get('tool_input'), dict) else {}
    target = next((tool_input[key] for key in ('file_path', 'notebook_path', 'subagent_type', 'to') if isinstance(tool_input.get(key), str)), None)
    if target is not None:
        prefix = str(ROOT) + '/'
        target = mask(target[len(prefix):] if target.startswith(prefix) else target)
    if permission:
        verdict = permission
    elif answer.get('decision') == 'block':
        verdict = 'block'
    elif code == 2:
        verdict = 'rc2'
    elif code != 0:
        verdict = 'falha'
    elif auto:
        verdict = 'auto'
    elif context:
        verdict = 'aponta'
    elif err.strip() and event == 'Stop':
        verdict = 'informa'
    else:
        verdict = 'passa'
    reason = specific.get('permissionDecisionReason') or answer.get('reason') or context
    if not reason and (code != 0 or event == 'Stop'):
        reason = next((line for line in err.splitlines() if line.strip()), None)
    notes = len(re.findall(r'AVISO \[[A-Za-z0-9]+\]|: R[0-9]+ ', out + '\n' + err))
    notes += len(re.findall(r'(?m)^- (?:ATENÇÃO|SETUP PENDENTE|BOOTSTRAP|ÁRVORE FORA|PENDENTE|Governança|Infra)', out))
    log(dict(ts=stamp(), sessao=payload.get('session_id'), quem=os.environ.get('HARNESS_QUEM') or payload.get('agent_type') or 'principal',
             hook=name[:-3], evento=event, ferramenta=payload.get('tool_name'), alvo=target, decisao=verdict,
             motivo=mask(reason) if isinstance(reason, str) else None, apontamentos=notes, rc=code, ms=elapsed))


def run_hook(name, args):
    """Run .claude/hooks/NAME with the same stdin, arguments, output and exit code. Missing hook fails closed (2)."""
    if not name or '/' in name or name.startswith(('.', '_')) or not name.endswith('.sh'):
        print(f"_run.sh: hook inválido: '{name}'", file=sys.stderr)
        return 2
    hook = HOOKS / name
    if not hook.is_file():
        print(f'_run.sh: hook ausente: {name}', file=sys.stderr)
        return 2
    data = sys.stdin.buffer.read()
    before = line_count(AUTO_LOG)
    start = time.monotonic()
    result = subprocess.run(['bash', str(hook), *args], input=data, capture_output=True)
    elapsed = int((time.monotonic() - start) * 1000)
    sys.stdout.buffer.write(result.stdout)
    sys.stdout.flush()
    sys.stderr.buffer.write(result.stderr)
    sys.stderr.flush()
    code = result.returncode if 0 <= result.returncode < 256 else 2
    try:
        # Approximate with parallel sessions: another session's line can mark this round as "auto".
        auto = name == 'bash-guard.sh' and line_count(AUTO_LOG) > before
        record(name, data.decode('utf-8', 'replace'), result.stdout.decode('utf-8', 'replace'), result.stderr.decode('utf-8', 'replace'), code, elapsed, auto)
    except Exception:  # noqa: BLE001 - measurement never decides
        pass
    return code


def git_hook(hook, script, args):
    """Run scripts/sdd/SCRIPT for a Git hook, showing its output as it comes and logging the round. Fails closed (1)."""
    if not re.fullmatch(r'[a-z-]+', hook or '') or not re.fullmatch(r'git-[a-z-]+\.sh', script or ''):
        print(f"git-hook-run: hook inválido: '{hook}' '{script}'", file=sys.stderr)
        return 1
    path = ROOT / 'scripts/sdd' / script
    if not path.is_file():
        print(f'git-hook-run: script ausente: {script}', file=sys.stderr)
        return 1
    start = time.monotonic()
    process = subprocess.Popen(['bash', str(path), *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = []
    for raw in process.stdout:
        sys.stdout.buffer.write(raw)
        sys.stdout.flush()
        lines.append(raw.decode('utf-8', 'replace').rstrip('\n'))
    code = process.wait()
    code = code if 0 <= code < 256 else 1
    try:
        shown = [line for line in lines if line.strip()]
        log(dict(ts=stamp(), sessao=None, quem='git', hook='git-' + hook, evento='git', ferramenta=None, alvo=None,
                 decisao='passa' if code == 0 else 'recusa', motivo=mask(shown[-1]) if code and shown else None,
                 apontamentos=len(re.findall(r'AVISO \[[A-Za-z0-9]+\]|: R[0-9]+ ', '\n'.join(lines))), rc=code,
                 ms=int((time.monotonic() - start) * 1000)))
    except Exception:  # noqa: BLE001
        pass
    return code


def percentile(values, share):
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * share)] if ordered else 0


def build_report(hours):
    rows, unreadable = [], 0
    folder = STATE / 'harness'
    for path in sorted(folder.glob('*.jsonl')) if folder.is_dir() else []:
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or not isinstance(row.get('ts'), str):
                    raise ValueError
                rows.append(row)
            except ValueError:
                unreadable += 1  # never dropped silently
    since = '0000' if hours == 0 else stamp(now() - timedelta(hours=hours))
    rows = [row for row in rows if row['ts'] >= since]
    interventions = [row for row in rows if row.get('decisao') in INTERVENTIONS]

    def tally(items, key):
        result = {}
        for item in items:
            label = str(item.get(key) if item.get(key) is not None else '?')
            result[label] = result.get(label, 0) + 1
        return result

    hooks = []
    for name in sorted({str(row.get('hook')) for row in rows}):
        own = [row for row in rows if str(row.get('hook')) == name]
        times = [int(row.get('ms') or 0) for row in own]
        hooks.append(dict(hook=name, rodadas=len(own), intervencoes=sum(1 for row in own if row.get('decisao') in INTERVENTIONS),
                          decisoes=tally(own, 'decisao'), apontamentos=sum(int(row.get('apontamentos') or 0) for row in own),
                          p50_ms=percentile(times, 0.5), p95_ms=percentile(times, 0.95), ms_total=sum(times)))
    hooks.sort(key=lambda item: -item['rodadas'])
    reasons = {}
    for row in rows:
        if row.get('decisao') in ('deny', 'ask', 'block', 'rc2', 'recusa', 'falha'):
            label = f"{row.get('hook')} · {str(row.get('motivo') or 'sem motivo')[:120]}"
            reasons[label] = reasons.get(label, 0) + 1
    # Insistence: the same denial repeated right after, in the same session (the agent retried what was denied).
    insistence, last = 0, {}
    for row in sorted((row for row in rows if row.get('sessao')), key=lambda item: item['ts']):
        key = (row.get('decisao'), row.get('hook'), row.get('motivo'))
        if row.get('decisao') in ('deny', 'block', 'rc2') and last.get(row['sessao']) == key:
            insistence += 1
        last[row['sessao']] = key
    return dict(janela='tudo' if hours == 0 else f'{hours} h', desde=since, rodadas=len(rows), ilegiveis=unreadable,
                intervencoes=len(interventions), taxa_intervencao=round(len(interventions) * 100 / len(rows), 1) if rows else 0,
                apontamentos=sum(int(row.get('apontamentos') or 0) for row in rows), ms_total=sum(int(row.get('ms') or 0) for row in rows),
                por_decisao=tally(rows, 'decisao'), por_hook=hooks,
                motivos=[dict(motivo=label, vezes=count) for label, count in sorted(reasons.items(), key=lambda item: -item[1])[:10]],
                insistencia=insistence, por_quem=tally(rows, 'quem'),
                conferidos_total=line_count(STATE / 'governance-ack.log') + line_count(STATE / 'infra-ack.log'),
                auto_aprovados_total=line_count(AUTO_LOG))


def report(args):
    hours, fmt = 168, 'texto'
    while args:
        flag = args.pop(0)
        if flag == '--horas' and args and args[0].isdigit():
            hours = int(args.pop(0))
        elif flag == '--tudo':
            hours = 0
        elif flag == '--json':
            fmt = 'json'
        elif flag == '--resumo':
            fmt = 'resumo'
        else:
            print('Uso: harness-report.sh [--horas N | --tudo] [--json] [--resumo]', file=sys.stderr)
            return 64
    data = build_report(hours)
    if fmt == 'json':
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif fmt == 'resumo':
        if not data['rodadas']:
            print(f"- Harness ({data['janela']}): nenhuma rodada registrada em .sdd/harness/.")
        else:
            decisions = data['por_decisao']
            print(f"- Harness ({data['janela']}): {data['rodadas']} rodadas, {data['intervencoes']} intervenções ({data['taxa_intervencao']}%: "
                  f"{decisions.get('deny', 0)} negações, {decisions.get('block', 0)} bloqueios, {decisions.get('aponta', 0)} apontamentos), "
                  f"{data['insistencia']} insistência(s), {data['ms_total'] // 1000} s nos hooks — make harness.")
    else:
        pairs = lambda mapping: ' · '.join(f'{key} {value}' for key, value in mapping.items()) or 'nada'  # noqa: E731
        print(f"Harness — janela: {data['janela']} (desde {data['desde'][:16]})")
        print(f"  rodadas: {data['rodadas']} · intervenções: {data['intervencoes']} ({data['taxa_intervencao']}%) · apontamentos: {data['apontamentos']} · "
              f"tempo nos hooks: {round(data['ms_total'] / 1000, 1)} s" + (f" · LINHAS ILEGÍVEIS: {data['ilegiveis']}" if data['ilegiveis'] else ''))
        print('  por decisão: ' + pairs(data['por_decisao']))
        print('  por quem: ' + pairs(data['por_quem']))
        print('\nPor hook (rodadas · intervenções · apontamentos · p50/p95 ms · total s · decisões)')
        for item in data['por_hook']:
            print(f"  {item['hook']}: {item['rodadas']} · {item['intervencoes']} · {item['apontamentos']} · {item['p50_ms']}/{item['p95_ms']} · "
                  f"{round(item['ms_total'] / 1000, 1)} · " + ', '.join(f'{key} {value}' for key, value in item['decisoes'].items()))
        print('\nMotivos que mais negaram ou bloquearam')
        for item in data['motivos'] or [dict(vezes=0, motivo='nenhum')]:
            print(f"  {item['vezes']}× {item['motivo']}" if item['vezes'] else '  nenhum')
        print(f"\nInsistência (a mesma negação seguida, na mesma sessão): {data['insistencia']}")
        print(f"Registros de \"conferido\" (total): {data['conferidos_total']} · auto-aprovados pelo guard Bash (total): {data['auto_aprovados_total']}")
    return 0


# --- check verdict ------------------------------------------------------------------------------------------------

def git_out(*args):
    result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def verdict_file():
    """The main checkout's .sdd/check-verdict, shared by its linked worktrees."""
    common = git_out('rev-parse', '--git-common-dir')
    if common:
        path = Path(common) if Path(common).is_absolute() else ROOT / common
        if path.name == '.git':
            return path.resolve().parent / '.sdd/check-verdict'
    return STATE / 'check-verdict'


def head_sha():
    return git_out('rev-parse', '--short=8', 'HEAD') or ''


def tree_is_clean():
    return git_out('status', '--porcelain') == ''  # unreadable (None) counts as dirty


def make_does_not_run():
    """make -n/-t/-q test nothing and -i swallows failures: such a run never writes a verdict."""
    letters = ''
    for position, word in enumerate(os.environ.get('MAKEFLAGS', '').split()):
        if word == '--':
            break
        if word.startswith('--') or ('=' in word and not word.startswith('-')):
            continue
        if word.startswith('-') or position == 0:
            letters += re.split(r'[CEIOWfjlo]', word.lstrip('-'), maxsplit=1)[0]
    return any(letter in letters for letter in 'ntqi')


def read_verdict():
    data = {}
    try:
        for line in verdict_file().read_text().splitlines():
            key, _, value = line.partition('=')
            data.setdefault(key, value)
    except OSError:
        return None
    return data


def describe():
    """One sentence about the last verdict against this tree's HEAD; second value is True only for green on this HEAD."""
    data, head = read_verdict(), head_sha()
    if data is None:
        return 'nenhum make check gravou veredito ainda', False
    code = data.get('exit', '')
    if not code.isdigit():
        return 'o veredito do make check não se lê', False
    state = 'verde' if code == '0' else f"VERMELHO (exit {code}; falharam: {data.get('failed') or 'sem a lista'})"
    when, sha = data.get('when', '?'), data.get('sha', '')
    if sha and sha == head:
        return f'o último make check ({when}) está {state} no HEAD ({head})', code == '0'
    return f"o último make check ({when}) está {state} em {sha or 'commit desconhecido'}, e o HEAD ({head or 'desconhecido'}) ainda não tem veredito", False


def verdict_run(command):
    if not command:
        print('Uso: check-verdict.sh run COMANDO… | show', file=sys.stderr)
        return 64
    if make_does_not_run():
        return subprocess.call(command)
    start_sha, start_clean = head_sha(), tree_is_clean()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = []
    for raw in process.stdout:
        sys.stdout.buffer.write(raw)
        sys.stdout.flush()
        lines.append(raw.decode('utf-8', 'replace'))
    code = process.wait()
    if code < 0 or code > 128:
        return 128 - code if code < 0 else code  # killed by a signal: the run did not finish and says nothing
    sha = start_sha
    if sha and (not start_clean or head_sha() != sha or not tree_is_clean()):
        sha += '-suja'  # the commit vouches for the run only if the tree matched it from start to end
    failed = []
    if code:
        for line in lines:
            match = re.match(r'(?:FAIL|ERROR): (\S+)', line) or re.match(r'g?make(?:\[\d+\])?: \*\*\* \[(?:[^\]]*: *)?([A-Za-z0-9_-]+)\]', line)
            if match and match.group(1) not in failed and not match.group(1).startswith('_'):
                failed.append(match.group(1))
    target = verdict_file()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', dir=target.parent, prefix='.check-verdict.', delete=False) as handle:
            handle.write(f"sha={sha}\nexit={code}\nfailed={','.join(failed)}\nwhen={stamp()}\n")
        Path(handle.name).replace(target)  # replaced at once: a reader never sees half of it
        print('check-verdict: ' + describe()[0])
    except OSError:
        print(f'check-verdict: não consegui gravar o veredito em {target}; o antigo, se houver, ficou como estava', file=sys.stderr)
    return code


# --- junction check -----------------------------------------------------------------------------------------------

def junction(base):
    """Run only the fences (harness.json) that read a file changed since BASE. 1 = a fence failed; 2 = git or config unreadable."""
    try:
        fences = config()['fences']
    except ValueError as exc:
        print(f'junction-check: {exc}', file=sys.stderr)
        return 2
    changed = set()
    for args in (['rev-parse', '--verify', '--quiet', base + '^{commit}'], ['diff', '--no-renames', '--name-only', f'{base}...HEAD'],
                 ['diff', '--no-renames', '--name-only', 'HEAD'], ['ls-files', '--others', '--exclude-standard']):
        out = git_out(*args)
        if out is None:  # a git that fails is never an empty diff
            print(f"junction-check: git {' '.join(args)} falhou (a base '{base}' existe?)", file=sys.stderr)
            return 2
        if args[0] != 'rev-parse':
            changed.update(line for line in out.splitlines() if line)
    print(f'junction-check: base {base}, {len(changed)} arquivo(s) mudado(s)', flush=True)
    if not fences:
        print('junction-check: nenhuma trava em .claude/harness.json (fences); nada rodou')
        return 0
    failed = ran = 0
    for fence in fences:
        name = fence['name']
        hit = next((path for path in sorted(changed) for prefix in fence['paths'] if prefix == '.' or path == prefix or path.startswith(prefix.rstrip('/') + '/')), None)
        if hit is None:
            print(f"pulada   {name} — nenhum arquivo mudado em: {' '.join(fence['paths'])}", flush=True)
            continue
        ran += 1
        with tempfile.NamedTemporaryFile('w+', prefix=f'junction-{name}-', suffix='.log', delete=False) as handle:
            print(f'rodando  {name} — log: {handle.name}', flush=True)
            start = time.monotonic()
            try:
                code = subprocess.run(fence['run'], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT,
                                      env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')).returncode
            except OSError as exc:
                handle.write(f'{exc}\n')
                code = 127
            took = int(time.monotonic() - start)
            if code == 0:
                print(f'ok       {name} ({took} s) — {hit}', flush=True)
                handle.close()
                os.unlink(handle.name)
            else:
                failed = 1
                handle.seek(0)
                tail = handle.read().splitlines()[-8:]
                print(f'FALHOU   {name} ({took} s, status {code}) — {hit}')
                print('\n'.join('         | ' + line for line in tail), flush=True)
    print(f"junction-check: {ran} trava(s) rodada(s){', com falha' if failed else ', todas verdes' if ran else ''}")
    return failed


def main():
    command, *args = sys.argv[1:] or ['']
    if command == 'run':
        return run_hook(args[0] if args else '', args[1:])
    if command == 'git-hook':
        return git_hook(args[0] if args else '', args[1] if len(args) > 1 else '', args[2:])
    if command == 'report':
        return report(list(args))
    if command == 'verdict':
        if args[:1] == ['run']:
            return verdict_run(args[1:])
        if args == ['show']:
            print(describe()[0])
            return 0
        print('Uso: check-verdict.sh run COMANDO… | show', file=sys.stderr)
        return 64
    if command == 'junction':
        return junction(args[0] if args else 'origin/main')
    if command == 'stage':
        print(stage())
        return 0
    print('harness.py: comando desconhecido', file=sys.stderr)
    return 64


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - the runner fails closed
        print(f'harness: erro interno: {exc}', file=sys.stderr)
        sys.exit(1 if sys.argv[1:2] == ['git-hook'] else 2)
