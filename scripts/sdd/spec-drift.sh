#!/usr/bin/env bash
# Drift: (1) hash_mismatch  (2) missing (arquivo sumiu)  (3) missing_from_index (spec em disco fora do índice). Exit 1 se houver.
source "$(dirname "$0")/_lib.sh"
[ -f "$INDEX" ] || { echo "sem índice — rode scripts/sdd/spec-index.sh"; exit 1; }
rc=0
while IFS=$'\t' read -r id path h; do
  if [ ! -f "$ROOT/$path" ]; then echo "missing: $id ($path)"; rc=1
  elif [ "$(sha "$ROOT/$path")" != "$h" ]; then echo "hash_mismatch: $id ($path)"; rc=1; fi
done < <(jq -r '.artifacts[] as $a | "\($a.id)\t\($a.path)\t\(.hashes[$a.id])"' "$INDEX")
while IFS= read -r f; do rel="${f#$ROOT/}"
  jq -e --arg p "$rel" '.artifacts[]|select(.path==$p)' "$INDEX" >/dev/null || { echo "missing_from_index: $rel"; rc=1; }
done < <(list_specs)
[ $rc -eq 0 ] && echo "spec-drift: OK ($(jq '.artifacts|length' "$INDEX") artefatos)" || echo "→ corrija e rode scripts/sdd/spec-index.sh (commite .specs/index.json junto)"
exit $rc
