---
name: sdd-status
description: Mostra o estado SDD do repositório — feature ativa, drift, specs por status, ADRs, clarificações abertas, gatilho de reconciliação. Use quando o usuário perguntar "como está o repo", "o que está pendente", "tem drift?".
allowed-tools: Bash(bash .claude/hooks/*), Bash(scripts/sdd/*), Bash(ls *), Bash(git log *), Bash(grep *), Bash(sort *), Bash(uniq *), Read, Grep
---
!`bash .claude/hooks/session-start.sh`

Specs por status: !`grep -h '^status:' .specs/features/F-*/spec.md .specs/components/C-*/spec.md 2>/dev/null | sort | uniq -c`

Resuma o acima em 5 linhas e proponha a próxima ação (spec a promover, drift a corrigir, postmortem devido).
