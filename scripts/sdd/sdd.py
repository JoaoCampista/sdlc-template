#!/usr/bin/env python3
"""Deterministic SDD plumbing. Standard library only; never executes product commands."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2])).resolve()
ID = re.compile(r'(?:F|C)-[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*')


def git(*args, root=ROOT, data=None):
    return subprocess.run(['git', '-C', str(root), *args], input=data, capture_output=True, check=True).stdout


def frontmatter(path):
    lines = Path(path).read_text().splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        raise ValueError(f'{path}: frontmatter ausente ou não terminado')
    result = {}
    for line in lines[1:lines[1:].index('---') + 1]:
        match = re.match(r'^([a-z_]+):\s*(.*?)\s*$', line)
        if match:
            key, value = match.groups()
            if key in result:
                raise ValueError(f'{path}: campo duplicado {key}')
            result[key] = value.strip('"\'')
    return result


def sha(data):
    return hashlib.sha256(data.replace(b'\r', b'')).hexdigest()


def catalog(root=ROOT):
    artifacts, hashes = [], {}
    paths = sorted((root / '.specs').rglob('*.md'), key=lambda p: p.relative_to(root).as_posix().encode())
    for path in paths:
        if '_TEMPLATE' in path.parts or 'postmortems' in path.parts or path.name in ('_TEMPLATE.md', 'ADR-000-template.md', 'README.md'):
            continue
        if path.is_symlink() or root not in path.resolve().parents:
            raise ValueError(f'spec fora da árvore: {path}')
        fm = frontmatter(path)
        for key in ('id', 'kind', 'status'):
            if not fm.get(key):
                raise ValueError(f'{path}: falta {key}')
        if fm['status'] not in {'draft', 'in_review', 'approved', 'deprecated', 'accepted', 'superseded'}:
            raise ValueError(f"status inválido: {fm['status']}")
        if fm['id'] in hashes:
            raise ValueError(f"duplicate_id: {fm['id']}")
        artifacts.append(dict(id=fm['id'], path=path.relative_to(root).as_posix(), kind=fm['kind'], status=fm['status']))
        hashes[fm['id']] = sha(path.read_bytes())
    return dict(artifacts=artifacts, hashes=hashes)


def index():
    target = ROOT / '.specs/index.json'
    entries = catalog()
    lint([ROOT / item['path'] for item in entries['artifacts']])
    content = (json.dumps(entries, ensure_ascii=False, indent=2) + '\n').encode()
    if target.exists() and target.read_bytes() == content:
        print('index: sem mudança')
        return
    if target.is_symlink():
        raise ValueError('index.json não pode ser symlink')
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temp:
        name = Path(temp.name)
        temp.write(content)
    try:
        name.chmod(0o644)
        name.replace(target)
    finally:
        name.unlink(missing_ok=True)
    print('index: atualizado')


def drift():
    stored = json.loads((ROOT / '.specs/index.json').read_text())
    expected = catalog()
    if stored != expected:
        raise ValueError('spec-drift: índice divergente (conteúdo, inclusão, remoção ou metadados); rode make sdd e versione specs + índice juntos')
    print(f"spec-drift: OK ({len(expected['artifacts'])} artefatos)")


def active(root=ROOT):
    path = root / '.sdd/active-spec'
    if not path.exists():
        return ''
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            if not ID.fullmatch(line):
                raise ValueError('ID inválido em .sdd/active-spec')
            return line
    return ''


def spec_path(identifier, root=ROOT):
    if not ID.fullmatch(identifier):
        raise ValueError('ID de spec inválido')
    for folder in ('features', 'components'):
        path = root / '.specs' / folder / identifier / 'spec.md'
        if path.is_file():
            return path
    raise ValueError(f'spec ativa inexistente: {identifier}')


def code_reason(root=ROOT):
    if os.environ.get('SDD_ALLOW_TRIVIAL') == '1':
        return ''
    identifier = active(root)
    if not identifier:
        return 'Spec antes de código: nenhuma spec ativa. /spec-new → G1 → .sdd/active-spec.'
    spec = spec_path(identifier, root)
    fm = frontmatter(spec)
    if fm.get('id') != identifier or fm.get('status') not in ('in_review', 'approved'):
        return f'{identifier}: código exige id correspondente e status in_review ou approved.'
    return ''


def snapshot(tree, destination):
    """Materialize tracked regular files only; never follow a staged symlink."""
    for record in git('ls-tree', '-rz', tree).split(b'\0'):
        if not record:
            continue
        meta, raw_path = record.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        rel = Path(os.fsdecode(raw_path))
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('caminho inválido no Git')
        if mode == '120000' or kind != 'blob':
            if rel.parts[0] in ('.specs', 'scripts'):
                raise ValueError(f'validação não segue symlink/submódulo: {rel}')
            continue
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(git('cat-file', 'blob', oid))
        path.chmod(0o755 if mode == '100755' else 0o644)


def validate_tree(tree):
    with tempfile.TemporaryDirectory(prefix='sdd-stage-') as temp:
        root = Path(temp)
        snapshot(tree, root)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), PYTHONDONTWRITEBYTECODE='1')
        for script in ('spec-lint-all.sh', 'spec-drift.sh'):
            subprocess.run(['bash', str(root / 'scripts/sdd' / script)], cwd=root, env=env, check=True)


def precommit():
    validate_tree(git('write-tree').decode().strip())


def prepare(message, source=''):
    if source in ('merge', 'squash'):
        return
    identifier = active()
    if not identifier:
        return
    content = None
    for kind in ('features', 'components'):
        path = f'.specs/{kind}/{identifier}/spec.md'
        try:
            content = git('show', ':' + path)
            break
        except subprocess.CalledProcessError:
            continue
    if content is None:
        raise ValueError('spec ativa ausente do stage; não é possível vincular o commit')
    target = Path(message)
    # Replace only the managed hash, preserving user Refs such as task and AC IDs.
    lines = target.read_text().splitlines()
    refs = [line for line in lines if line.startswith('Refs:')]
    body = [line for line in lines if not line.startswith(('Spec-Hash:', 'Refs:'))]
    if not any(identifier in line.split() for line in refs):
        refs.append(f'Refs: {identifier}')
    trailers = refs + [f'Spec-Hash: sha256:{sha(content)}']
    target.write_text('\n'.join(body).rstrip() + '\n\n' + '\n'.join(trailers) + '\n')


def prepush():
    # The stdin protocol names the actual commits being sent, not the working tree.
    seen = set()
    for line in sys.stdin:
        fields = line.split()
        if len(fields) != 4:
            raise ValueError('pre-push: protocolo inválido')
        _, local_oid, _, _ = fields
        if set(local_oid) == {'0'} or local_oid in seen:
            continue
        seen.add(local_oid)
        validate_tree(local_oid)


def install_hooks():
    result = subprocess.run(['git', '-C', str(ROOT), 'config', '--get', 'core.hooksPath'], capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError('não foi possível ler core.hooksPath')
    if result.returncode == 0:
        raise ValueError('core.hooksPath configurado: integre os hooks existentes; setup não o altera')
    hookdir = Path(os.fsdecode(git('rev-parse', '--git-path', 'hooks')).strip())
    if not hookdir.is_absolute():
        hookdir = ROOT / hookdir
    pairs = {'commit-msg': 'git-commit-msg.sh', 'prepare-commit-msg': 'git-prepare-commit-msg.sh', 'pre-commit': 'git-pre-commit.sh', 'pre-push': 'git-pre-push.sh'}
    generated = {}
    for hook, script in pairs.items():
        path = hookdir / hook
        body = f'#!/usr/bin/env bash\n# sdd-template managed hook\nR=$(git rev-parse --show-toplevel) || exit 1\nexport CLAUDE_PROJECT_DIR="$R"\nexec bash "$R/scripts/sdd/{script}" "$@"\n'
        if path.exists() or path.is_symlink():
            old = path.read_text()
            legacy = '#!/usr/bin/env bash\nR=$(git rev-parse --show-toplevel)\nexec bash "$R/scripts/sdd/'
            legacy_scripts = set(pairs.values()) | {'spec-drift.sh'}
            is_legacy = any(old == legacy + name + '" "$@"\n' for name in legacy_scripts)
            if path.is_symlink() or ('# sdd-template managed hook' not in old and not is_legacy):
                raise ValueError(f'hook preexistente preservado: {path}; integre-o explicitamente')
        generated[path] = body
    hookdir.mkdir(parents=True, exist_ok=True)
    for path, body in generated.items():
        path.write_text(body)
        path.chmod(0o755)
    print('git hooks instalados (inclui worktrees)')


def session():
    print('## Estado SDD')
    try:
        identifier = active()
        print('- Feature ativa: ' + (identifier or 'NENHUMA'))
        reason = code_reason()
        if reason:
            print('- ' + reason)
        if identifier:
            print('- A spec ativa só cobre as ACs dela; encerrou a tarefa, limpe .sdd/active-spec.')
            for pm in (ROOT / '.specs/postmortems').glob('PM-*.md'):
                if frontmatter(pm).get('parent') == identifier and 'feature-close' in pm.read_text():
                    print('- ATENÇÃO: spec ativa já tem postmortem de fechamento.')
        if frontmatter(ROOT / '.specs/product/product-spec.md').get('bootstrap') == 'pending':
            print('- BOOTSTRAP PENDENTE: definir produto e stack; tooling não é o produto.')
        if os.environ.get('SDD_ALLOW_TRIVIAL') == '1':
            print('- ATENÇÃO: SDD_ALLOW_TRIVIAL=1; sessão excepcional iniciada pelo humano.')
        for local in (ROOT / '.claude/settings.local.json', ROOT / '.claude/settings.json'):
            if local.exists() and json.loads(local.read_text()).get('env', {}).get('SDD_ALLOW_TRIVIAL'):
                print('- ATENÇÃO: escape definido em settings; conferir com o humano.')
        drift()
    except (ValueError, OSError) as exc:
        print('- PENDENTE: ' + str(exc))
    print('- Execute make doctor para conferir dependências e instalação. /sdd-status não prova disparo automático dos hooks.')
    print('- No Codex/outros clientes, AGENTS.md e Git continuam válidos; estes hooks são do Claude Code.')


def stop(payload):
    if not isinstance(payload.get('stop_hook_active', False), bool):
        raise ValueError('stop_hook_active deve ser booleano')
    problems = []
    try:
        if json.loads((ROOT / '.specs/index.json').read_text()) != catalog():
            problems.append('DRIFT: rode make sdd, confira e versione as specs e o índice juntos.')
    except (ValueError, OSError) as exc:
        problems.append('DRIFT: ' + str(exc))
    # Count the most recent uninterrupted run of commits without a spec change.
    history = git('log', '--since=1 hour ago', '--format=%H').decode().splitlines() if has_head() else []
    count = 0
    for commit in history:
        paths = git('diff-tree', '--root', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines()
        if any(path.startswith('.specs/') for path in paths):
            break
        count += 1
    if count >= 3:
        problems.append(f'GATILHO 12.1: {count} commits consecutivos sem specs na última hora; reconcilie antes de encerrar.')
    if problems and not payload.get('stop_hook_active', False):
        print(json.dumps(dict(decision='block', reason=' '.join(problems))))
    else:
        if problems:
            print('Stop já avisado: ' + ' '.join(problems), file=sys.stderr)
        print('{}')


def has_head():
    return subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', '-q', 'HEAD'], capture_output=True).returncode == 0


def lint(paths):
    errors = []
    for raw in paths:
        path = Path(raw)
        if '_TEMPLATE' in path.parts or path.name in ('_TEMPLATE.md', 'ADR-000-template.md', 'README.md'):
            continue
        try:
            fm = frontmatter(path)
            content = path.read_text()
            def require(ok, message):
                if not ok: errors.append(f'{path}: {message}')
            for key in ('id', 'kind', 'title', 'parent', 'version', 'status', 'last_updated'):
                require(fm.get(key), f'R1 falta {key}')
            kind, status = fm.get('kind'), fm.get('status')
            valid = {'adr': ('in_review', 'accepted', 'superseded', 'deprecated'), 'postmortem': ('draft', 'approved', 'corrected')}.get(kind, ('draft', 'in_review', 'approved', 'deprecated'))
            require(status in valid, 'R1 status inválido')
            require(re.fullmatch(r'(F|C|PROD|CONST|ADR|PLAN|TASKS|RISK|PM|DS|DESIGN)-[A-Za-z0-9]+([-_][A-Za-z0-9]+)*', fm.get('id', '')), 'R1 id inválido')
            require(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', fm.get('version', '')), 'R1 semver inválido')
            require(not re.search(r'<[^<>]*(?: |:|YYYY|DOMINIO|NOME|Título|Tema|slug|path|time|nomes?|papel|ação|valor|explícito|contrato|alternativa|delta|link|lição|escopo|data|descrição|kind|erro|…)[^<>]*>', content), 'R1 placeholder não preenchido')
            sections = {
                'feature_spec': ['WHAT/HOW', 'User Stories', 'Acceptance Criteria', 'NFRs', 'NEEDS_CLARIFICATION'],
                'component_spec': ['WHAT/HOW', 'User Stories', 'Acceptance Criteria', 'NFRs', 'NEEDS_CLARIFICATION'],
                'adr': ['Contexto', 'Decisão', 'Consequências', 'Alternativas consideradas', 'Riscos', 'Fences contra regressão', 'Revisões'],
                'design_system_spec': ['Escopo', 'Regras', 'Enforcement', 'Exemplos canônicos', 'Anti-padrões', 'Changelog'],
                'design': ['Referências', 'Estado por estado', 'Diferenças conhecidas', 'Lacunas', 'Conferência visual'],
                'postmortem': ['§1', '§2', '§3', '§4', '§5', '§6', '§7'],
                'plan': [], 'tasks': [], 'risks': [], 'constitution': [], 'product_spec': [],
            }
            require(kind in sections, 'R1 kind desconhecido')
            for section in sections.get(kind, []):
                require(re.search(r'^## ' + re.escape(section) + r'(?:[ .—]|$)', content, re.M), f'R2 falta seção {section}')
            if kind in ('feature_spec', 'component_spec'):
                acs = re.findall(r'^- \*\*(AC-[0-9]+[a-z]?)\.\*\* (.+)$', content, re.M)
                require(acs, 'R3 nenhuma AC')
                require(len({ac for ac, _ in acs}) == len(acs), 'R3 AC duplicada')
                for ac, body in acs:
                    tests = re.findall(r'@test:([^ )`]+)', body)
                    require(tests, f'R3 {ac} sem @test')
                    for test in tests:
                        target = (ROOT / test).resolve()
                        require(ROOT in target.parents, 'R5 @test fora do projeto')
                        if status == 'approved': require(target.is_file(), f'R5 @test não existe: {test}')
                if status == 'approved':
                    section = content.split('## NEEDS_CLARIFICATION', 1)[-1].split('\n## ', 1)[0]
                    require(all(line.strip() in ('', '- nenhum', '- none') for line in section.splitlines()), 'R4 NEEDS_CLARIFICATION aberto')
            if kind == 'design':
                require(fm.get('applicable') in ('true', 'false'), 'R1 design exige applicable: true|false')
                require(fm.get('parent', '').startswith(('F-', 'C-')), 'R1 design deve referenciar feature/componente')
            if kind == 'tasks':
                rows = [line for line in content.splitlines() if re.match(r'^\| T-[0-9]+ \|', line)]
                require(rows, 'R3 tasks sem tarefas')
                for row in rows: require(re.search(r'AC-[0-9]+', row), 'R3 task sem AC')
            if kind == 'design_system_spec':
                rules = re.findall(r'^\d+\. \*\*(R[0-9]+)', content, re.M)
                require(rules, 'R2 DS sem regras')
                for rule in rules: require(re.search(r'^\| ' + rule + r' \|', content, re.M), f'R2 {rule} sem enforcement')
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    if errors: raise ValueError('\n'.join(errors))
    print('spec-lint: OK')


def main():
    command, *args = sys.argv[1:]
    if command == 'lint': lint(args)
    elif command == 'index': index()
    elif command == 'drift': drift()
    elif command == 'pre-commit': precommit()
    elif command == 'prepare': prepare(*args[:2])
    elif command == 'pre-push': prepush()
    elif command == 'install': install_hooks()
    elif command == 'session': session()
    elif command == 'stop':
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict): raise ValueError('entrada deve ser objeto JSON')
        stop(payload)
    else: raise ValueError('comando desconhecido')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'SDD: {exc}', file=sys.stderr)
        sys.exit(2 if sys.argv[1] in ('stop',) else 1)
