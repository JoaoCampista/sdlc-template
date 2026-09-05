#!/usr/bin/env bash
# Stop: relatório curto de drift + lembrete de reconciliação (Regra 12.1). Informativo, para o HUMANO no transcript; não bloqueia.
source "$(dirname "$0")/../../scripts/sdd/_lib.sh"
bash "$ROOT/scripts/sdd/spec-drift.sh" 2>&1 | tail -2
n=$(git -C "$ROOT" log --since='1 hour ago' --oneline 2>/dev/null | wc -l | tr -d ' ')
s=$(git -C "$ROOT" log --since='1 hour ago' --name-only --pretty=format: 2>/dev/null | grep -c '^\.specs/' || true)
[ "$n" -ge 3 ] && [ "$s" -eq 0 ] && echo "GATILHO 12.1: $n commits na última hora sem tocar .specs/ — pare e reconcilie (docs(specs): … Lote N)."
exit 0
