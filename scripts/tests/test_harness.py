import json
import os
from support import RepoCase, SOURCE


class Harness(RepoCase):
    def run_hook(self, name, payload, *args, ok=True):
        return self.run_script('.claude/hooks/_run.sh', name, *args, data=json.dumps(payload), ok=ok)

    def bash(self, command, **extra):
        result = self.run_hook('bash-guard.sh', dict(hook_event_name='PreToolUse', tool_name='Bash', cwd=str(self.root), tool_input=dict(command=command), **extra))
        return json.loads(result.stdout).get('hookSpecificOutput', {}).get('permissionDecision')

    def edit(self, path, **extra):
        result = self.run_hook('pre-edit-guard.sh', dict(hook_event_name='PreToolUse', tool_name='Write', cwd=str(self.root), tool_input=dict(file_path=str(self.root / path)), **extra))
        return json.loads(result.stdout).get('hookSpecificOutput', {}).get('permissionDecision')

    def test_runner_same_answer_logs_round_and_fails_closed(self):
        """AC-9: same output and code through the runner, one masked line per round, never the command."""
        secret = 'A' * 40
        payload = dict(hook_event_name='PreToolUse', session_id='s1', tool_name='Write', cwd=str(self.root), tool_input=dict(file_path=str(self.root / 'src/app.py'), content=secret))
        direct = self.hook('pre-edit-guard.sh', payload)
        through = self.run_hook('pre-edit-guard.sh', payload)
        self.assertEqual(direct.stdout, through.stdout)
        rows = self.log_rows()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row['hook'], row['decisao'], row['alvo'], row['quem'], row['sessao'], row['rc']), ('pre-edit-guard', 'deny', 'src/app.py', 'principal', 's1', 0))
        self.assertIn('spec', row['motivo'].lower())
        self.bash(f'echo {secret} > docs/a.md')
        raw = ''.join(path.read_text() for path in (self.root / '.sdd/harness').glob('*.jsonl'))
        self.assertNotIn(secret, raw)
        self.assertNotIn('echo', raw)
        # Exit code and stderr of a failing hook pass through; the round is still logged.
        broken = self.run_script('.claude/hooks/_run.sh', 'pre-edit-guard.sh', data='broken', ok=False)
        self.assertEqual(broken.returncode, 2)
        self.assertEqual(self.log_rows()[-1]['decisao'], 'rc2')
        for name in ('missing.sh', '../x.sh', '_run.sh', ''):
            result = self.run_script('.claude/hooks/_run.sh', name, data='{}', ok=False)
            self.assertEqual((result.returncode, result.stdout), (2, ''), name)

    def test_report_counts_interventions_insistence_and_unreadable(self):
        """AC-9: the report measures what the log holds; an unreadable line is counted, never dropped."""
        payload = dict(hook_event_name='PreToolUse', session_id='s1', tool_name='Write', cwd=str(self.root), tool_input=dict(file_path=str(self.root / 'src/app.py')))
        for _ in range(3): self.run_hook('pre-edit-guard.sh', payload)
        self.run_hook('pre-edit-guard.sh', dict(payload, tool_input=dict(file_path=str(self.root / 'docs/a.md'))))
        log = next((self.root / '.sdd/harness').glob('*.jsonl'))
        log.write_text(log.read_text() + 'not json\n')
        data = json.loads(self.run_script('scripts/sdd/harness-report.sh', '--json', '--tudo').stdout)
        self.assertEqual((data['rodadas'], data['intervencoes'], data['insistencia'], data['ilegiveis']), (4, 3, 2, 1))
        self.assertEqual(data['por_decisao'], {'deny': 3, 'passa': 1})
        self.assertIn('4 rodadas', self.run_script('scripts/sdd/harness-report.sh', '--resumo').stdout)
        self.assertIn('LINHAS ILEGÍVEIS: 1', self.run_script('scripts/sdd/harness-report.sh').stdout)
        self.assertEqual(self.run_script('scripts/sdd/harness-report.sh', '--bogus', ok=False).returncode, 64)

    def test_stage_decides_what_asked_the_human(self):
        """AC-10: beta asks; development denies what stays with the human and logs what it lets through."""
        opaque, held = 'python3 -c "print(1)"', 'git reset --hard'
        for value in (None, 'beta', 'producao'):
            if value: self.stage(value)
            self.assertEqual((self.bash(opaque), self.bash(held), self.edit('.claude/hooks/guard.py')), ('ask', 'ask', 'ask'), value)
        (self.root / '.claude/deploy-stage.json').write_text('{broken')
        self.assertEqual(self.bash(opaque), 'ask')
        self.stage()
        self.assertIsNone(self.bash(opaque))
        self.assertEqual(self.log_rows()[-1]['decisao'], 'auto')
        line = (self.root / '.sdd/auto-aprovado.log').read_text()
        self.assertIn('Programa opaco', line)
        for command in (held, 'docker compose down -v', 'psql -c "DROP TABLE users"', 'echo x > .claude/settings.json', 'cp a .claude/hooks/guard.py'):
            self.assertEqual(self.bash(command), 'deny', command)
        self.assertIsNone(self.edit('.claude/hooks/guard.py'))
        # The auto-approval log names the program, never the command text (it may carry a credential).
        self.assertIsNone(self.bash('PGPASSWORD=hunter2-prod python3 x.py --token ghp.short/abc'))
        logged = (self.root / '.sdd/auto-aprovado.log').read_text()
        self.assertNotIn('hunter2', logged); self.assertNotIn('ghp.short', logged); self.assertIn('\tpython3\t', logged)
        # A construct the guard cannot read never turns a deny or a hold into a pass.
        for command in ('git reset --hard $(true)', 'git add -A $(true)', 'git commit --no-verify -m "$(echo x)"', 'SDD_ALLOW_TRIVIAL=1 echo `true`',
                        'echo x > .claude/deploy-stage.json; env true', 'echo x > .claude/hooks/guard.py; cd a b', 'echo x > .claude/hooks/guard.py $(true)',
                        'psql -c "DROP TABLE t" ${DB}', 'echo x > src/app.py $(true)', 'rm -rf .claude', 'mv .claude ../x', 'mv scripts ../x',
                        'git rev-parse HEAD > .sdd/governance-head', 'printf sha=x > .sdd/check-verdict', 'make check | tee /dev/null | tail'):
            self.assertEqual(self.bash(command), 'deny', command)
        self.assertEqual(self.bash('echo x > .claude/hooks/guard.py $(true)', agent_type='produto'), 'deny')
        self.assertEqual(self.bash('bash scripts/sdd/governance-sync.sh ack ok', agent_type='produto'), 'deny')
        self.assertIsNone(self.bash('bash scripts/sdd/governance-sync.sh ack ok'))
        self.assertEqual(self.edit('.sdd/roles/arquiteto-head'), 'deny')
        self.assertIsNone(self.edit('.sdd/active-spec'))
        self.assertIsNone(self.bash('echo $(date) 2>/dev/null'))
        self.assertIsNone(self.bash('echo F-EXAMPLE-V1 > .sdd/active-spec'))
        self.activate()
        self.assertIsNone(self.bash('echo x > src/app.py $(true)'))  # with an active spec, only logged
        self.assertEqual(self.bash('rm -rf .claude'), 'deny')
        # Changing the stage always goes to the human, by Edit and by the shell.
        self.assertEqual(self.edit('.claude/deploy-stage.json'), 'ask')
        self.assertEqual(self.bash('echo x > .claude/deploy-stage.json'), 'deny')
        self.assertEqual(self.bash('git add -f x'), 'deny')

    def test_long_run_in_a_pipe_needs_tee(self):
        """AC-11: the whole output of a long run stays in a file."""
        for command in ('make check | tail -5', 'make test 2>&1 | grep FAIL', 'make check | grep x | tee out.log', 'make -j2 test-mutations | head'):
            self.assertEqual(self.bash(command), 'deny', command)
        for command in ('make check > docs/check.log 2>&1', 'make check 2>&1 | tee docs/check.log | tail -5', 'make sdd | tail -3', 'make check'):
            self.assertIsNone(self.bash(command), command)

    def test_check_verdict_records_result_and_head(self):
        """AC-11: green or red, with the commit; a dirty tree does not vouch for the commit."""
        self.baseline()
        head = self.git('rev-parse', '--short=8', 'HEAD').stdout.strip()
        show = lambda: self.run_script('scripts/sdd/check-verdict.sh', 'show').stdout
        self.assertIn('nenhum make check', show())
        self.assertEqual(self.run_script('scripts/sdd/check-verdict.sh', 'run', 'bash', '-c', 'echo ok').returncode, 0)
        self.assertIn(f'verde no HEAD ({head})', show())
        self.assertIn(f'sha={head}\nexit=0\n', (self.root / '.sdd/check-verdict').read_text())
        red = self.run_script('scripts/sdd/check-verdict.sh', 'run', 'bash', '-c', 'echo "FAIL: test_x (suite.Case.test_x)"; exit 3', ok=False)
        self.assertEqual(red.returncode, 3)
        self.assertIn('FAIL: test_x', red.stdout)
        self.assertIn('VERMELHO (exit 3; falharam: test_x)', show())
        self.run_script('scripts/sdd/check-verdict.sh', 'run', 'true')
        self.assertIn('verde no HEAD', show())
        (self.root / 'tests/example.py').write_text('changed\n')
        self.assertIn('a árvore mudou depois', show())  # a green verdict does not vouch for later edits
        self.run_script('scripts/sdd/check-verdict.sh', 'run', 'true')
        self.assertIn(f'sha={head}-suja', (self.root / '.sdd/check-verdict').read_text())
        self.assertIn('ainda não tem veredito', show())
        before = (self.root / '.sdd/check-verdict').read_text()
        self.run_script('scripts/sdd/check-verdict.sh', 'run', 'false', env=dict(self.env, MAKEFLAGS='n'), ok=False)
        self.assertEqual(before, (self.root / '.sdd/check-verdict').read_text())
        self.assertIn('make check:', self.hook('session-start.sh', {}).stdout)

    def test_junction_runs_only_fences_that_read_changes(self):
        """AC-11: skipped, green and red fences; an unreadable base fails closed."""
        self.harness_config(fences=[dict(name='docs', run=['bash', '-c', 'echo ran'], paths=['docs']),
                                    dict(name='tests', run=['bash', '-c', 'echo broke; exit 1'], paths=['tests'])])
        self.baseline()
        base = self.git('rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(self.run_script('scripts/sdd/junction-check.sh', 'no-such-base', ok=False).returncode, 2)
        result = self.run_script('scripts/sdd/junction-check.sh', base)
        self.assertIn('pulada   docs', result.stdout)
        self.assertIn('pulada   tests', result.stdout)
        (self.root / 'docs').mkdir()
        (self.root / 'docs/new.md').write_text('x\n')
        result = self.run_script('scripts/sdd/junction-check.sh', base)
        self.assertIn('ok       docs', result.stdout)
        (self.root / 'tests/example.py').write_text('changed\n')
        result = self.run_script('scripts/sdd/junction-check.sh', base, ok=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('FALHOU   tests', result.stdout)
        self.assertIn('| broke', result.stdout)
        (self.root / '.claude/harness.json').write_text('[]')
        self.assertEqual(self.run_script('scripts/sdd/junction-check.sh', base, ok=False).returncode, 2)

    def codex(self, event, payload, ok=True):
        return self.run_script('scripts/sdd/codex-hook.sh', event, data=json.dumps(dict(hook_event_name=event, cwd=str(self.root), **payload)), ok=ok)

    def test_codex_adapter_translates_and_refuses(self):
        """AC-16: canonical decisions, ask becomes deny, invalid payload or grammar exits 2."""
        patch = lambda body: dict(tool_name='apply_patch', tool_input=dict(command=body))
        decision = lambda result: json.loads(result.stdout).get('hookSpecificOutput', {}).get('permissionDecision')
        code = '*** Begin Patch\n*** Add File: src/app.py\n+print(1)\n*** End Patch\n'
        docs = '*** Begin Patch\n*** Update File: docs/a.md\n@@\n-old\n+new\n*** End Patch\n'
        self.assertEqual(decision(self.codex('PreToolUse', patch(code))), 'deny')
        self.assertEqual(json.loads(self.codex('PreToolUse', patch(docs)).stdout), {})
        self.activate()
        self.assertEqual(json.loads(self.codex('PreToolUse', patch(code)).stdout), {})
        moved = '*** Begin Patch\n*** Update File: docs/a.md\n*** Move to: .claude/hooks/guard.py\n@@\n-old\n+new\n*** End Patch\n'
        self.assertEqual(decision(self.codex('PreToolUse', patch(moved))), 'deny')  # never the main session
        asked = self.codex('PreToolUse', dict(tool_name='Bash', tool_input=dict(command='python3 -c "print(1)"')))
        self.assertEqual(decision(asked), 'deny')
        self.assertIn('não implementa ask', asked.stdout)
        self.assertEqual(json.loads(self.codex('PreToolUse', dict(tool_name='Bash', tool_input=dict(command='git status --short'))).stdout), {})
        for body in ('*** Begin Patch\n*** Add File:  .claude/settings.json\n+x\n*** End Patch\n', '*** Begin Patch\n*** Add File: ~/x\n+x\n*** End Patch\n',
                     '*** Begin Patch\n*** End Patch\n', code + 'trailing\n', '*** Begin Patch\n*** Update File: a.md\n*** End Patch\n', 'garbage'):
            self.assertEqual(self.codex('PreToolUse', patch(body), ok=False).returncode, 2, body)
        self.assertEqual(self.codex('PostToolUse', patch(docs), ok=False).returncode, 2)
        self.assertEqual(self.codex('PreToolUse', dict(tool_name='Other', tool_input=dict(command='x')), ok=False).returncode, 2)
        self.assertEqual(self.run_script('scripts/sdd/codex-hook.sh', 'PreToolUse', data=json.dumps(dict(hook_event_name='Stop', cwd=str(self.root))), ok=False).returncode, 2)
        self.assertEqual(self.run_script('scripts/sdd/codex-hook.sh', 'Stop', data=json.dumps(dict(hook_event_name='Stop', cwd='/', stop_hook_active=False)), ok=False).returncode, 2)
        self.assertIn('Estado SDD', json.loads(self.codex('SessionStart', dict(source='startup')).stdout)['hookSpecificOutput']['additionalContext'])
        self.assertEqual(json.loads(self.codex('Stop', dict(stop_hook_active=False)).stdout), {})
        (self.root / '.specs/index.json').write_text('{}')
        self.assertEqual(json.loads(self.codex('Stop', dict(stop_hook_active=False)).stdout)['decision'], 'block')
        self.assertTrue(all(row['quem'] == 'codex' for row in self.log_rows()))

    def test_codex_installer_is_idempotent_and_preserves_other_file(self):
        """AC-16: creates once, keeps an equivalent file, refuses to overwrite a different one."""
        self.run_script('scripts/sdd/install-codex-hooks.sh')
        target = self.root / '.codex/hooks.json'
        created = target.read_text()
        self.assertIn('codex-hook.sh', created)
        self.assertIn('preservada', self.run_script('scripts/sdd/install-codex-hooks.sh').stdout)
        target.write_text('{"hooks": {}}')
        self.assertEqual(self.run_script('scripts/sdd/install-codex-hooks.sh', ok=False).returncode, 2)
        self.assertEqual(target.read_text(), '{"hooks": {}}')

    def test_distributed_configuration_is_inert_and_valid(self):
        """AC-8/10/13: the template ships no stage, no role paths and no IaC roots."""
        self.assertFalse((SOURCE / '.claude/deploy-stage.json').exists())
        config = json.loads((SOURCE / '.claude/harness.json').read_text())
        self.assertTrue(all(role['paths'] == [] for role in config['roles'].values()))
        self.assertEqual(config['infra_roots'], [])
        for role in config['roles']:
            self.assertTrue((SOURCE / '.claude/agents' / f'{role}.md').is_file(), role)
        for fence in config['fences']:
            self.assertTrue(os.path.exists(SOURCE / 'scripts/tests' / fence['run'][-1]), fence['name'])
