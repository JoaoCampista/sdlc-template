#!/usr/bin/env bash
source "$(dirname "$0")/_lib.sh"
# portável em bash 3.2 (macOS): sem mapfile
files=()
while IFS= read -r f; do [ -n "$f" ] && files+=("$f"); done < <(
  list_specs
  find "$SPECS/postmortems" -name '*.md' -not -name '_TEMPLATE.md' 2>/dev/null
)
[ ${#files[@]} -eq 0 ] && { echo "spec-lint-all: nenhum artefato"; exit 0; }
bash "$(dirname "$0")/spec-lint.sh" "${files[@]}"
