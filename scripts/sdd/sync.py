#!/usr/bin/env python3
"""Records that keep up with the work: upper documents, role marks, applied IaC, task status and the panel.

Standard library only. Git failures raise (callers fail closed); nothing here runs product commands.
"""
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd import ROOT, frontmatter, git  # noqa: E402
import harness  # noqa: E402

SPECS = ROOT / '.specs'
CONST = SPECS / 'constitution/constitution.md'
PROD = SPECS / 'product/product-spec.md'
STATE = ROOT / '.sdd'
FID = r'F-[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*'
IAC_SUFFIXES = ['.tf', '.tftpl', '.hcl', '.json', '.tfvars.example']


def text_git(*args):
    return git(*args).decode('utf-8', 'replace')


def head():
    result = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', '-q', 'HEAD'], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ''


def valid_mark(mark, tip):
    """The mark is a commit in the history of HEAD."""
    if not re.fullmatch(r'[0-9a-f]{7,64}', mark or ''):
        return False
    for args in (['cat-file', '-e', mark + '^{commit}'], ['merge-base', '--is-ancestor', mark, tip]):
        if subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True).returncode != 0:
            return False
    return True


def read_mark(path):
    try:
        return path.read_text().split('\n', 1)[0].strip()
    except OSError:
        return None


def fm_text(text, key):
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return ''
    for line in lines[1:]:
        if line == '---':
            break
        if line.startswith(key + ':'):
            return line[len(key) + 1:].strip().strip('"\'')
    return ''


def fm_value(path, key):
    try:
        return frontmatter(path).get(key, '')
    except (ValueError, OSError):
        return ''


def needs_items(text):
    """Non-empty lines of the NEEDS_CLARIFICATION section, apart from "- nenhum"."""
    if '## NEEDS_CLARIFICATION' not in text:
        return 0
    section = text.split('## NEEDS_CLARIFICATION', 1)[1].split('\n## ', 1)[0].splitlines()[1:]
    return sum(1 for line in section if line.strip() and not re.match(r'\s*- ?(nenhum|none)\b', line))


def task_rows(text):
    """(id, status) of each task row; the status is the "Status" column of the header, else the last filled cell."""
    column, rows = None, []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if line.startswith('|') and column is None and 'Status' in cells:
            column = cells.index('Status')
        if re.match(r'^\| *T-[0-9]+ ', line):
            filled = [cell for cell in cells if cell]
            status = cells[column] if column is not None and column < len(cells) else (filled[-1] if filled else '')
            rows.append((cells[0], status))
    return rows


def is_open(status):
    return not status.startswith(('done', 'deferred', '~~'))


def feature_specs():
    return [path for path in sorted((SPECS / 'features').glob('*/spec.md')) if '_TEMPLATE' not in path.parts]


def bootstrap_pending():
    return fm_value(PROD, 'bootstrap') == 'pending'


# --- upper documents (governance) ---------------------------------------------------------------------------------

def governance_report():
    lines, needs, missing, stale = [], [], [], []
    product = PROD.read_text() if PROD.is_file() else ''
    for spec in feature_specs():
        identifier, status = fm_value(spec, 'id'), fm_value(spec, 'status')
        if identifier and identifier not in product:
            missing.append(identifier)
        count = needs_items(spec.read_text())
        if status in ('in_review', 'approved') and count:
            needs.append(f'{identifier} {count}')
    if needs:
        lines.append(f"- Governança, linhas na NEEDS_CLARIFICATION que o approved recusa (R4): {', '.join(needs)} — trate durante a feature, não no fim.")
    if missing and not bootstrap_pending():
        lines.append(f"- Governança, o product-spec não cita: {', '.join(missing)} — leve ao produto.")
    constitution = CONST.read_text() if CONST.is_file() else ''
    const_date = fm_text(constitution, 'last_updated')
    for adr in sorted((SPECS / 'adr').glob('ADR-[0-9]*.md')):
        identifier, date = fm_value(adr, 'id'), fm_value(adr, 'last_updated')
        if identifier and identifier in constitution and date and const_date and date > const_date:
            stale.append(f'{identifier} ({date})')
    if stale:
        lines.append(f"- Governança, a Constitution (de {const_date}) cita ADRs revisadas depois: {', '.join(stale)} — confira (bash scripts/sdd/governance-sync.sh ack MOTIVO se nada muda).")
    return lines


def governance_check(mark):
    """Findings between MARK and HEAD, one per line. Git failures raise."""
    changed = [line for line in text_git('diff', '--name-only', mark, 'HEAD', '--', '.specs').splitlines() if line]
    prod_touched = '.specs/product/product-spec.md' in changed
    const_touched = '.specs/constitution/constitution.md' in changed
    constitution = CONST.read_text() if CONST.is_file() else ''
    findings = []
    for name in changed:
        path = ROOT / name
        if not path.is_file():
            continue
        if re.fullmatch(r'\.specs/features/[^/]+/spec\.md', name) and '_TEMPLATE' not in name:
            previous = subprocess.run(['git', '-C', str(ROOT), 'show', f'{mark}:{name}'], capture_output=True)
            before = fm_text(previous.stdout.decode('utf-8', 'replace'), 'status') if previous.returncode == 0 else ''
            after = fm_value(path, 'status')
            if before != after and not prod_touched and not bootstrap_pending():
                findings.append(f"PROD {fm_value(path, 'id')} {before or 'nova'} → {after}, e o product-spec não mudou")
        elif re.fullmatch(r'\.specs/adr/ADR-[0-9][^/]*\.md', name) and not name.endswith('ADR-000-template.md') and not const_touched:
            identifier = fm_value(path, 'id')
            if subprocess.run(['git', '-C', str(ROOT), 'cat-file', '-e', f'{mark}:{name}'], capture_output=True).returncode != 0:
                findings.append(f'CONST {identifier} é nova, e a Constitution não mudou (confira se ela a cita)')
            elif identifier and identifier in constitution:
                findings.append(f'CONST {identifier}, citada pela Constitution, mudou, e a Constitution não')
        elif re.fullmatch(r'\.specs/features/[^/]+/tasks\.md', name) and '_TEMPLATE' not in name:
            spec = path.parent / 'spec.md'
            if spec.is_file() and not any(is_open(status) for _, status in task_rows(path.read_text())):
                count = needs_items(spec.read_text())
                if count:
                    findings.append(f"NEEDS {fm_value(spec, 'id')} sem task aberta e com {count} linha(s) na NEEDS_CLARIFICATION")
    return findings


def write_ack(log_name, tip, reason, hook):
    STATE.mkdir(exist_ok=True)
    with open(STATE / log_name, 'a', encoding='utf-8') as handle:
        handle.write(f'{harness.stamp()} {tip[:8]} {reason}\n')
    # The "conferido" also goes to the harness log, to measure how often a block was dismissed this way.
    harness.log(dict(ts=harness.stamp(), sessao=None, quem='principal', hook=hook, evento='ack', ferramenta=None, alvo=None,
                     decisao='ack', motivo=harness.mask(reason), apontamentos=0, rc=0, ms=0))


def governance_ack(reason):
    tip = head()
    if not reason.strip() or not tip:
        raise ValueError('ack pede o motivo e um HEAD legível')
    STATE.mkdir(exist_ok=True)
    (STATE / 'governance-head').write_text(tip + '\n')
    write_ack('governance-ack.log', tip, reason, 'governance-ack')
    print(f'governance-sync: conferido até {tip[:8]} ({reason})')


# --- roles: paths that a subagent owns the picture of --------------------------------------------------------------

def role_file(role, suffix):
    return STATE / 'roles' / f'{role}-{suffix}'


def digest_only(mark, name):
    """Outside image digests nothing changed between the mark and HEAD (a redeploy does not change the design)."""
    sides = []
    for revision in (mark, 'HEAD'):
        result = subprocess.run(['git', '-C', str(ROOT), 'show', f'{revision}:{name}'], capture_output=True)
        if result.returncode != 0:
            return False  # new, deleted or unreadable on one side counts as a change
        sides.append(result.stdout)
    normal = [re.sub(rb'sha256:[0-9a-f]{64}', b'sha256:DIGEST', side) for side in sides]
    return sides[0] != sides[1] and normal[0] == normal[1]


def role_findings():
    tip, findings = head(), []
    for role, spec in sorted(harness.config()['roles'].items()):
        paths = spec.get('paths', [])
        if not paths:
            continue  # nothing configured yet (before the stack exists): inert
        call = f"chame o subagente {role} (ferramenta Agent, subagent_type {role}) para {spec.get('pedido', 'conferir o que mudou e relatar as divergências')}"
        mark = read_mark(role_file(role, 'head'))
        if mark is None:
            findings.append(f'{role.upper()} SEM REGISTRO: não há .sdd/roles/{role}-head — {call}.')
            continue
        if not valid_mark(mark, tip):
            findings.append(f'{role.upper()} COM REGISTRO INVÁLIDO: .sdd/roles/{role}-head não é um commit do histórico do HEAD — {call}.')
            continue
        changed = [name for name in text_git('diff', '--name-only', mark, 'HEAD', '--', *paths).splitlines() if name and not digest_only(mark, name)]
        if changed:
            findings.append(f"MUDOU sem o {role}: {len(changed)} arquivo(s) desde {mark[:8]} ({' '.join(changed[:5])}) — {call}.")
    return findings


# --- infrastructure as code and what is applied ---------------------------------------------------------------------

def infra_roots():
    return harness.config()['infra_roots']


def infra_changes(mark, root):
    names = text_git('diff', '--name-only', mark, 'HEAD', '--', root['dir'], *[f':(exclude){item}' for item in root.get('exclude', [])]).splitlines()
    suffixes = tuple(root.get('suffixes', IAC_SUFFIXES))
    return [name for name in names if name.endswith(suffixes)]


def infra_check():
    findings = []
    if not head():
        raise ValueError('o HEAD não foi lido')
    for root in infra_roots():
        if not (ROOT / root['dir']).is_dir():
            continue
        mark = read_mark(STATE / 'infra-applied' / root['name'])
        if mark is None:
            findings.append(f"INFRA {root['dir']} sem registro de apply")
        elif not valid_mark(mark, 'HEAD'):
            findings.append(f"INFRA {root['dir']} com marca inválida")
        else:
            changed = infra_changes(mark, root)
            if changed:
                findings.append(f"INFRA {root['dir']}: {len(changed)} arquivo(s) de IaC commitado(s) desde o apply de {mark[:8]} ({' '.join(changed[:3])})")
    return findings


def infra_root(directory):
    wanted = Path(directory)
    wanted = (wanted if wanted.is_absolute() else ROOT / wanted).resolve()
    for root in infra_roots():
        if (ROOT / root['dir']).resolve() == wanted:
            return root
    raise ValueError(f"{directory} não é uma raiz de infra_roots em .claude/harness.json")


def infra_set(root, tip):
    folder = STATE / 'infra-applied'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / root['name']).write_text(tip + '\n')


def infra_mark(directory):
    """Called by the project's apply script after a successful apply; only a root clean in git moves the mark."""
    root, tip = infra_root(directory), head()
    if not tip:
        raise ValueError('o HEAD não foi lido')
    scope = [root['dir'], *[f':(exclude){item}' for item in root.get('exclude', [])]]
    dirty = subprocess.run(['git', '-C', str(ROOT), 'diff', '--quiet', 'HEAD', '--', *scope]).returncode != 0
    if dirty or text_git('ls-files', '--others', '--exclude-standard', '--', *scope).strip():
        print(f"infra-sync: {root['dir']} tem mudança fora do commit: a marca do apply não sobe (commite e registre com ack)", file=sys.stderr)
        return
    infra_set(root, tip)
    print(f"infra-sync: {root['dir']} aplicado até {tip[:8]}")


def infra_ack(directory, reason):
    root, tip = infra_root(directory), head()
    if not reason.strip() or not tip:
        raise ValueError('Uso: infra-sync.sh ack RAIZ MOTIVO')
    infra_set(root, tip)
    write_ack('infra-ack.log', tip, f"{root['dir']} {reason}", 'infra-ack')
    print(f"infra-sync: {root['dir']} conferido até {tip[:8]} ({reason})")


def infra_report():
    try:
        findings = infra_check()
    except (ValueError, subprocess.CalledProcessError) as exc:
        return [f'- INFRA ILEGÍVEL: {exc}.']
    if not findings:
        return []
    return ['- Infra commitada sem apply: ' + '; '.join(item[len('INFRA '):] for item in findings) + ' — rode o plano e o apply, ou bash scripts/sdd/infra-sync.sh ack RAIZ MOTIVO.']


# --- task status goes up with the code -----------------------------------------------------------------------------

def task_sync(base, tip):
    """A code commit that cites a task (F-ID … T-NNN) goes up with that feature's tasks.md changed in the same push."""
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', '--quiet', tip + '^{commit}'], capture_output=True, check=True)
    span = [tip, '--not', '--remotes'] if base == '--novos' else [f'{base}..{tip}']
    commits = text_git('rev-list', '--no-merges', *span).split()
    touched = set(text_git('log', '-m', '--format=', '--name-only', *span, '--', '.specs/features').split('\n'))
    failures, features = [], []
    for commit in commits:
        files = text_git('diff-tree', '--root', '--no-commit-id', '--name-only', '-r', commit).splitlines()
        if all(name.startswith('.specs/') for name in files):
            continue  # the record itself
        message = text_git('log', '-1', '--format=%B', commit)
        for feature in sorted({match.group(1) for match in re.finditer(rf'({FID})[^;)]*?T-[0-9]{{3}}', message)}):
            tasks = f'.specs/features/{feature}/tasks.md'
            if text_git('ls-tree', '--name-only', tip, '--', tasks).strip() != tasks:
                continue  # a feature without tasks.md has no status to keep
            if feature not in features:
                features.append(feature)
            if tasks not in touched:
                subject = text_git('log', '-1', '--format=%h %s', commit).strip()[:90]
                failures.append(f'→ o commit {subject} cita uma task da {feature}, e o {tasks} não muda neste push: atualize o status da task (AGENTS.md, Regra 12.8)')
    for feature in features:  # the reminder, never a refusal
        blocked = [identifier for identifier, status in task_rows(text_git('show', f'{tip}:.specs/features/{feature}/tasks.md')) if status.startswith('blocked')]
        if blocked:
            print(f"lembrete (task-sync): bloqueadas da {feature}: {' '.join(blocked)} — confira se o que as bloqueava já entrou")
    for line in failures:
        print(line)
    return 1 if failures else 0


# --- panel and setup -------------------------------------------------------------------------------------------------

def painel():
    print('Painel SDD (contagens derivadas agora; nada aqui é registro)')
    for spec in feature_specs():
        counts = {}
        tasks = spec.parent / 'tasks.md'
        rows = task_rows(tasks.read_text()) if tasks.is_file() else []
        for _, status in rows:
            word = 'lápide' if status.startswith('~~') else (status.split() or ['?'])[0].rstrip(':;,.')
            counts[word] = counts.get(word, 0) + 1
        summary = ', '.join(f'{word} {count}' for word, count in sorted(counts.items())) or 'sem tasks'
        print(f"- {fm_value(spec, 'id')} ({fm_value(spec, 'status')} v{fm_value(spec, 'version')}): {summary} · NEEDS abertas: {needs_items(spec.read_text())}")
        for identifier, status in rows:
            if status.startswith('blocked'):
                print(f'    bloqueada {identifier}: {status[:120]}')
    for line in governance_report() + infra_report():
        print(line)
    print('- Veredito: ' + harness.describe()[0])
    print('- Estágio: ' + harness.stage())


def init_marks():
    """Setup of a clone: with history and no mark yet, nothing local is pending, so the marks start at HEAD."""
    tip = head()
    if not tip:
        return
    targets = [STATE / 'governance-head'] + [role_file(role, 'head') for role in harness.config()['roles']]
    for target in targets:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(tip + '\n')


def main():
    area, *args = sys.argv[1:] or ['']
    if area == 'governance' and args[:1] == ['report']:
        print('\n'.join(governance_report()), end='\n' if governance_report() else '')
    elif area == 'governance' and args[:1] == ['check'] and len(args) == 2:
        for line in governance_check(args[1]):
            print(line)
    elif area == 'governance' and args[:1] == ['ack']:
        governance_ack(' '.join(args[1:]))
    elif area == 'infra' and args == ['check']:
        for line in infra_check():
            print(line)
    elif area == 'infra' and args[:1] == ['mark'] and len(args) == 2:
        infra_mark(args[1])
    elif area == 'infra' and args[:1] == ['ack'] and len(args) >= 3:
        infra_ack(args[1], ' '.join(args[2:]))
    elif area == 'infra' and args == ['report']:
        for line in infra_report():
            print(line)
    elif area == 'tasks' and len(args) == 2:
        return task_sync(*args)
    elif area == 'painel':
        painel()
    elif area == 'init-marks':
        init_marks()
    else:
        print('Uso: sync.py governance report|check MARCA|ack MOTIVO · infra check|mark PASTA|ack RAIZ MOTIVO|report · tasks BASE HEAD · painel', file=sys.stderr)
        return 64
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'sync: {exc}', file=sys.stderr)
        sys.exit(1 if sys.argv[1:2] == ['tasks'] else 2)
