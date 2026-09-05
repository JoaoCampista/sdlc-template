#!/usr/bin/env bash
# Reconstrói .specs/index.json: {artifacts:[{id,path,kind,status}], hashes:{id:sha256}}. Escritor único do índice.
source "$(dirname "$0")/_lib.sh"
tmp=$(mktemp); echo '{"artifacts":[],"hashes":{}}' > "$tmp"
dups=0; seen=""
while IFS= read -r f; do
  id=$(fm "$f" id); kind=$(fm "$f" kind); status=$(fm "$f" status); rel="${f#$ROOT/}"
  [ -z "$id" ] && { echo "AVISO: sem id no frontmatter: $rel" >&2; continue; }
  case " $seen " in *" $id "*) echo "ERRO duplicate_id: $id ($rel)" >&2; dups=1;; esac; seen="$seen $id"
  h=$(sha "$f")
  jq --arg id "$id" --arg p "$rel" --arg k "$kind" --arg s "$status" --arg h "$h" \
     '.artifacts += [{id:$id,path:$p,kind:$k,status:$s}] | .hashes[$id]=$h' "$tmp" > "$tmp.2" && mv "$tmp.2" "$tmp"
done < <(list_specs)
jq --arg d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '. + {generated_at:$d}' "$tmp" > "$tmp.final" && mv "$tmp.final" "$INDEX"; rm -f "$tmp"
echo "index: $(jq '.artifacts|length' "$INDEX") artefatos → ${INDEX#$ROOT/}"
exit $dups
