import json
import os
from pathlib import Path
from support import RepoCase, feature

ADR = '---\nid: ADR-002\nkind: adr\ntitle: Stack\nparent: PROD-001\nversion: 1.0.0\nstatus: accepted\nlast_updated: 2026-11-01\n---\n## Contexto\nx\n## Decisão\nx\n## Consequências\nx\n## Alternativas consideradas\nx\n## Riscos\nx\n## Fences contra regressão\nx\n## Revisões\n- nenhuma\n'
CONST = '---\nid: CONST-001\nkind: constitution\ntitle: Constitution\nparent: PROD-001\nversion: 1.0.0\nstatus: in_review\nlast_updated: 2026-10-26\n---\nStack: ADR-002.\n'
TASKS = '---\nid: TASKS-F-EXAMPLE-V1\nkind: tasks\ntitle: Tasks\nparent: F-EXAMPLE-V1\nversion: 0.1.0\nstatus: in_review\nlast_updated: 2026-10-26\n---\n| ID | Descrição | AC | Status | Evidência |\n|---|---|---|---|---|\n| T-001 | Works | AC-1 | {status} | |\n'


class Team(RepoCase):
    def setUp(self):
        super().setUp()
        self.spec = self.root / '.specs/features/F-EXAMPLE-V1/spec.md'
        self.product = self.root / '.specs/product/product-spec.md'
        self.product.write_text(self.product.read_text().replace('bootstrap: pending', 'bootstrap: complete'))
        self.tasks = self.root / '.specs/features/F-EXAMPLE-V1/tasks.md'
        self.tasks.write_text(TASKS.format(status='todo'))
        self.reindex()

    def reindex(self):
        self.run_script('scripts/sdd/spec-index.sh')

    def stop(self, script, active=False, ok=True):
        result = self.hook(script, dict(stop_hook_active=active), ok=ok)
        return json.loads(result.stdout).get('reason', ''), result

    def save(self, message='docs: specs'):
        self.reindex()
        return self.commit(message, '.specs')

    def test_governance_blocks_stale_upper_documents(self):
        """AC-12: status change without the product-spec, cited ADR without the Constitution, open NEEDS without open task."""
        self.assertEqual(self.stop('governance-check.sh')[0], '')  # no history: nothing to compare
        self.baseline()
        self.assertIn('SEM REGISTRO', self.stop('governance-check.sh')[0])
        self.run_script('scripts/setup.sh')  # setup starts the marks at HEAD
        mark = self.root / '.sdd/governance-head'
        self.assertEqual(self.stop('governance-check.sh')[0], '')
        self.spec.write_text(feature(status='approved'))
        head = self.save()
        reason, _ = self.stop('governance-check.sh')
        self.assertIn('PROD F-EXAMPLE-V1 in_review → approved', reason)
        self.assertNotEqual(mark.read_text().strip(), head)  # a finding never advances the mark
        reason, result = self.stop('governance-check.sh', active=True)
        self.assertEqual(reason, '')
        self.assertIn('ATRASADOS', result.stderr)
        self.assertNotEqual(self.run_script('scripts/sdd/governance-sync.sh', 'ack', ok=False).returncode, 0)
        self.run_script('scripts/sdd/governance-sync.sh', 'ack', 'conferido: sem mudança de escopo')
        self.assertEqual(self.stop('governance-check.sh')[0], '')
        self.assertIn('sem mudança de escopo', (self.root / '.sdd/governance-ack.log').read_text())
        self.assertEqual(self.log_rows()[-1]['decisao'], 'ack')
        # The same change together with the product-spec passes and advances the mark.
        self.spec.write_text(feature(status='in_review'))
        self.product.write_text(self.product.read_text() + '\nF-EXAMPLE-V1 voltou.\n')
        head = self.save()
        self.assertEqual(self.stop('governance-check.sh')[0], '')
        self.assertEqual(mark.read_text().strip(), head)
        # ADR: new, then changed while cited by the Constitution.
        (self.root / '.specs/adr').mkdir()
        (self.root / '.specs/constitution').mkdir()
        (self.root / '.specs/constitution/constitution.md').write_text(CONST)
        self.save()
        self.assertEqual(self.stop('governance-check.sh')[0], '')
        (self.root / '.specs/adr/ADR-002-stack.md').write_text(ADR)
        self.save()
        self.assertIn('CONST ADR-002 é nova', self.stop('governance-check.sh')[0])
        self.run_script('scripts/sdd/governance-sync.sh', 'ack', 'a Constitution já cita')
        (self.root / '.specs/adr/ADR-002-stack.md').write_text(ADR.replace('- nenhuma', '- 2026-11-12: revisão'))
        self.save()
        self.assertIn('CONST ADR-002, citada pela Constitution, mudou', self.stop('governance-check.sh')[0])
        self.run_script('scripts/sdd/governance-sync.sh', 'ack', 'conferido')
        # NEEDS open with every task done.
        self.spec.write_text(feature().replace('- nenhum', '- Qual o limite?'))
        self.tasks.write_text(TASKS.format(status='done'))
        self.save()
        self.assertIn('NEEDS F-EXAMPLE-V1 sem task aberta', self.stop('governance-check.sh')[0])
        self.assertIn('F-EXAMPLE-V1 1', self.run_script('scripts/sdd/governance-sync.sh', 'report').stdout)
        mark.write_text('0' * 40 + '\n')
        self.assertIn('REGISTRO INVÁLIDO', self.stop('governance-check.sh')[0])

    def test_bootstrap_pending_has_no_product_to_keep_up(self):
        """AC-12: before the product exists, a feature status change is not a product finding."""
        self.product.write_text(self.product.read_text().replace('bootstrap: complete', 'bootstrap: pending'))
        self.reindex(); self.baseline(); self.run_script('scripts/setup.sh')
        self.spec.write_text(feature(status='approved'))
        self.save()
        self.assertEqual(self.stop('governance-check.sh')[0], '')

    def test_open_needs_warns_at_edit_and_at_session(self):
        """AC-12: the open clarification of an in_review spec is pointed out at once, without failing the edit."""
        self.activate()
        self.spec.write_text(feature().replace('- nenhum', '- Qual o limite?'))
        result = self.hook('post-spec-edit.sh', dict(cwd=str(self.root), tool_input=dict(file_path=str(self.spec))))
        self.assertIn('AVISO [R4]', json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])
        self.assertIn('1 NEEDS_CLARIFICATION aberta', self.hook('session-start.sh', {}).stdout)
        self.spec.write_text(feature())
        self.assertEqual(json.loads(self.hook('post-spec-edit.sh', dict(cwd=str(self.root), tool_input=dict(file_path=str(self.spec)))).stdout), {})

    def agent(self, event, role, call='toolu_1', response=None, **extra):
        payload = dict(hook_event_name=event, tool_name='Agent', tool_use_id=call, tool_input=dict(subagent_type=role), **extra)
        if response is not None: payload['tool_response'] = response
        return self.hook('role-mark.sh', payload)

    def test_role_paths_block_until_the_role_agent_ran(self):
        """AC-13: inert without paths; blocks without mark or with changes; only a call that ran advances the mark."""
        self.baseline()
        self.assertEqual(self.stop('role-check.sh')[0], '')  # nothing configured
        self.harness_config(roles=dict(arquiteto=dict(paths=['infra/', 'docs/architecture.md'], pedido='atualizar os diagramas')))
        self.assertIn('ARQUITETO SEM REGISTRO', self.stop('role-check.sh')[0])
        mark = self.root / '.sdd/roles/arquiteto-head'
        self.agent('PreToolUse', 'arquiteto')
        self.assertFalse(mark.exists())  # a request that was denied or failed never advances the mark
        self.agent('PostToolUse', 'arquiteto', response=dict(agentId='abcdef0123'))
        first = self.git('rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(mark.read_text().strip(), first)
        self.assertEqual(self.stop('role-check.sh')[0], '')
        (self.root / 'infra').mkdir()
        (self.root / 'infra/compose.yml').write_text('image: app@sha256:' + 'a' * 64 + '\n')
        (self.root / 'tests/example.py').write_text('other\n')
        self.commit('feat: infra', 'infra', 'tests')
        reason, _ = self.stop('role-check.sh')
        self.assertIn('MUDOU sem o arquiteto: 1 arquivo(s)', reason)
        self.assertIn('subagent_type arquiteto', reason)
        self.assertEqual(self.stop('role-check.sh', active=True)[0], '')
        # Other agents, subagent callers and a PostToolUse without its own PreToolUse do not move the mark.
        self.agent('PreToolUse', 'produto', call='toolu_2'); self.agent('PostToolUse', 'produto', call='toolu_2')
        self.agent('PreToolUse', 'arquiteto', call='toolu_3', agent_type='design'); self.agent('PostToolUse', 'arquiteto', call='toolu_3', agent_type='design')
        self.agent('PostToolUse', 'arquiteto', call='toolu_4')
        self.assertEqual(mark.read_text().strip(), first)
        # Continuing the same agent by SendMessage counts as a request.
        message = dict(tool_name='SendMessage', tool_use_id='toolu_5', tool_input=dict(to='abcdef0123'))
        self.hook('role-mark.sh', dict(hook_event_name='PreToolUse', **message))
        self.hook('role-mark.sh', dict(hook_event_name='PostToolUse', **message))
        self.assertEqual(self.stop('role-check.sh')[0], '')
        # Only an image digest changed: the design is the same.
        (self.root / 'infra/compose.yml').write_text('image: app@sha256:' + 'b' * 64 + '\n')
        self.commit('chore: digest', 'infra')
        self.assertEqual(self.stop('role-check.sh')[0], '')
        (self.root / '.claude/harness.json').write_text('{broken')
        self.assertIn('NÃO CONFERIDOS', self.stop('role-check.sh')[0])
        self.assertEqual(self.agent('PreToolUse', 'arquiteto', call='toolu_6').returncode, 0)  # the mark never blocks

    def test_committed_iac_blocks_once_until_applied_or_acknowledged(self):
        """AC-13: no mark or IaC after the mark blocks; the same finding blocks once; ack and mark clear it."""
        (self.root / 'infra/cloud').mkdir(parents=True)
        (self.root / 'infra/cloud/main.tf').write_text('resource "x" "y" {}\n')
        self.baseline(); self.commit('feat: iac', 'infra')
        self.assertEqual(self.stop('infra-check.sh')[0], '')  # no root configured
        self.harness_config(infra_roots=[dict(name='cloud', dir='infra/cloud')])
        self.assertIn('infra/cloud sem registro de apply', self.stop('infra-check.sh')[0])
        reason, result = self.stop('infra-check.sh')
        self.assertEqual(reason, '')  # same finding: informs, does not loop
        self.assertIn('SEM APPLY', result.stderr)
        self.assertIn('sem registro', self.run_script('scripts/sdd/infra-sync.sh', 'report').stdout)
        (self.root / 'infra/cloud/main.tf').write_text('resource "x" "z" {}\n')
        self.run_script('scripts/sdd/infra-sync.sh', 'mark', 'infra/cloud')
        self.assertFalse((self.root / '.sdd/infra-applied/cloud').exists())  # applied from a dirty disk: no mark
        self.commit('feat: iac 2', 'infra')
        self.run_script('scripts/sdd/infra-sync.sh', 'mark', 'infra/cloud')
        self.assertEqual(self.stop('infra-check.sh')[0], '')
        (self.root / 'infra/cloud/notes.md').write_text('not IaC\n'); self.commit('docs: notes', 'infra')
        self.assertEqual(self.stop('infra-check.sh')[0], '')
        (self.root / 'infra/cloud/main.tf').write_text('resource "x" "w" {}\n'); self.commit('feat: iac 3', 'infra')
        self.assertIn('1 arquivo(s) de IaC', self.stop('infra-check.sh')[0])
        self.assertNotEqual(self.run_script('scripts/sdd/infra-sync.sh', 'ack', 'infra/other', 'x', ok=False).returncode, 0)
        self.run_script('scripts/sdd/infra-sync.sh', 'ack', 'infra/cloud', 'plano sem mudança')
        self.assertEqual(self.stop('infra-check.sh')[0], '')
        self.assertIn('plano sem mudança', (self.root / '.sdd/infra-ack.log').read_text())

    def decision(self, result):
        return json.loads(result.stdout or '{}').get('hookSpecificOutput', {}).get('permissionDecision')

    def test_subagent_cannot_edit_enforcement_or_message_others(self):
        """AC-14: a subagent is denied on the enforcement in any stage and only talks to the main session."""
        self.activate(); self.stage()
        edit = lambda path, **extra: self.decision(self.hook('pre-edit-guard.sh', dict(tool_name='Edit', cwd=str(self.root), tool_input=dict(file_path=path), **extra)))
        for path in ('.claude/hooks/guard.py', '.claude/settings.json', '.claude/harness.json', 'scripts/sdd/sdd.py', '.github/workflows/ci.yml', '.claude/agents/spec-reviewer.md', '.claude/deploy-stage.json', '.codex/hooks.json'):
            self.assertEqual(edit(path, agent_type='produto'), 'deny', path)
            self.assertEqual(edit(path, agent_id='abc', agent_type=''), 'deny', path)
        self.assertIsNone(edit('.claude/hooks/guard.py'))
        self.assertIsNone(edit('src/app.py', agent_type='produto'))
        self.assertIsNone(edit('.claude/agents/produto.md', agent_type='produto'))
        send = lambda to, **extra: self.decision(self.hook('subagent-message-guard.sh', dict(tool_name='SendMessage', tool_input=dict(to=to), **extra)))
        self.assertEqual(send('other-session', agent_type='design'), 'deny')
        self.assertEqual(send('other-session', agent_id='abc', agent_type=''), 'deny')
        self.assertIsNone(send('main', agent_type='design'))
        self.assertIsNone(send('other-session'))
        self.assertEqual(self.run_script('.claude/hooks/subagent-message-guard.sh', data='[]', ok=False).returncode, 2)

    def test_reviewer_writes_only_memory_and_mutation_copy(self):
        """AC-14: by the real path; symlink, hard link, relative, dotted and in-repo scratch are denied."""
        scratch = Path(self.temp.name) / 'scratch'
        (scratch / 'spec-reviewer').mkdir(parents=True)
        memory = self.root / '.claude/agent-memory-local/spec-reviewer'
        memory.mkdir(parents=True)
        (self.root / 'src').mkdir()
        (self.root / 'src/app.py').write_text('x\n')
        def write(path, mode='', agent='spec-reviewer', scratchpad=scratch, tool='Write'):
            key = 'notebook_path' if tool == 'NotebookEdit' else 'file_path'
            payload = dict(tool_name=tool, agent_type=agent, scratchpad_dir=str(scratchpad), tool_input={key: str(path)})
            return self.decision(self.run_script('.claude/hooks/reviewer-guard.sh', *([mode] if mode else []), data=json.dumps(payload)))
        for mode in ('', 'settings'):
            self.assertIsNone(write(memory / 'note.md', mode))
            self.assertIsNone(write(scratch / 'spec-reviewer/mut-1/scripts/x.sh', mode))
            for path in (self.root / 'src/app.py', self.root / '.specs/features/F-EXAMPLE-V1/spec.md', memory / 'note.txt', scratch / 'other/x.sh',
                         'relative/x.md', f'{memory}/../../../src/app.py', self.root / 'docs/a.md'):
                self.assertEqual(write(path, mode), 'deny', str(path))
        (memory / 'link.md').symlink_to(self.root / 'src/app.py')
        self.assertEqual(write(memory / 'link.md'), 'deny')
        os.link(self.root / 'src/app.py', scratch / 'spec-reviewer/hard.py')
        self.assertEqual(write(scratch / 'spec-reviewer/hard.py'), 'deny')
        inside = self.root / 'tmp-scratch'
        (inside / 'spec-reviewer').mkdir(parents=True)
        self.assertEqual(write(inside / 'spec-reviewer/x.sh', scratchpad=inside), 'deny')
        self.assertEqual(write(scratch / 'spec-reviewer/x.sh', scratchpad='relative'), 'deny')
        self.assertEqual(write(memory / 'note.md', tool='Bash'), 'deny')
        # In the settings wiring it only applies to the reviewer; the frontmatter wiring always applies.
        self.assertIsNone(write(self.root / 'src/app.py', 'settings', agent='produto'))
        self.assertEqual(write(self.root / 'src/app.py', '', agent=''), 'deny')
        self.assertEqual(self.run_script('.claude/hooks/reviewer-guard.sh', 'bogus', data='{}', ok=False).returncode, 2)

    def push(self, base, head):
        return self.run_script('scripts/sdd/task-sync.sh', base, head, ok=False)

    def test_code_that_cites_a_task_goes_up_with_tasks_md(self):
        """AC-15: refused without the tasks.md of the cited feature in the same push; the record itself passes."""
        self.baseline()
        base = self.git('rev-parse', 'HEAD').stdout.strip()
        (self.root / 'tests/example.py').write_text('# one\n')
        code = self.commit('feat(app): works (F-EXAMPLE-V1 AC-1, T-001)', 'tests')
        result = self.push(base, code)
        self.assertEqual(result.returncode, 1)
        self.assertIn('cita uma task da F-EXAMPLE-V1', result.stdout)
        # A new ref: only the commits no remote has are read (the baseline, with its tasks.md, is already there).
        self.git('update-ref', 'refs/remotes/origin/main', base)
        self.assertEqual(self.push('--novos', code).returncode, 1)
        zeros = '0' * 40
        self.assertNotEqual(self.run_script('scripts/sdd/git-pre-push.sh', data=f'refs/heads/main {code} refs/heads/main {zeros}\n', ok=False).returncode, 0)
        self.tasks.write_text(TASKS.format(status='blocked: espera a T-002'))
        record = self.save('docs(specs): F-EXAMPLE-V1 tasks')
        result = self.push(base, record)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('bloqueadas da F-EXAMPLE-V1: T-001', result.stdout)
        self.run_script('scripts/sdd/git-pre-push.sh', data=f'refs/heads/main {record} refs/heads/main {base}\n')
        # A commit that cites no task, or another feature without tasks.md, is not held.
        (self.root / 'tests/example.py').write_text('# two\n')
        other = self.commit('fix(app): typo (F-OTHER-V1 T-009); refs F-EXAMPLE-V1', 'tests')
        self.assertEqual(self.push(record, other).returncode, 0)
        self.assertEqual(self.push(base, 'no-such-commit').returncode, 1)

    def test_git_hooks_run_through_the_logging_runner(self):
        """AC-15: installed hooks keep their effect and leave a line per round."""
        self.baseline(); self.install()
        (self.root / 'tests/example.py').write_text('# changed\n')
        self.git('add', 'tests/example.py')
        self.assertNotEqual(self.git('commit', '-qm', 'not conventional', ok=False).returncode, 0)
        self.git('commit', '-qm', 'test: conventional')
        rows = [row for row in self.log_rows() if row['quem'] == 'git']
        self.assertIn(('git-commit-msg', 'recusa'), [(row['hook'], row['decisao']) for row in rows])
        self.assertIn(('git-pre-commit', 'passa'), [(row['hook'], row['decisao']) for row in rows])
        self.assertEqual(self.run_script('scripts/sdd/git-hook-run.sh', 'pre-commit', '../evil.sh', ok=False).returncode, 1)

    def test_panel_derives_task_states(self):
        """AC-12: the panel reads the true state of each task and the open clarifications."""
        self.tasks.write_text(TASKS.format(status='blocked: espera a infra'))
        out = self.run_script('scripts/sdd/painel.sh').stdout
        self.assertIn('F-EXAMPLE-V1 (in_review v0.1.0): blocked 1 · NEEDS abertas: 0', out)
        self.assertIn('bloqueada T-001', out)
