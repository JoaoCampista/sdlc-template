#!/usr/bin/env bash
# Funções comuns dos scripts SDD. Dependências: bash, jq, sha256sum|shasum, awk, grep.
set -u   # sem -e/pipefail: hooks devem ser defensivos; scripts controlam rc explicitamente
command -v jq >/dev/null || { echo "jq ausente — scripts SDD inoperantes; instale jq (brew install jq / apt install jq)" >&2; exit 2; }
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
SPECS="$ROOT/.specs"
INDEX="$SPECS/index.json"
sha() { if command -v sha256sum >/dev/null; then tr -d '\r' < "$1" | sha256sum | cut -d' ' -f1; else tr -d '\r' < "$1" | shasum -a 256 | cut -d' ' -f1; fi; }
fm() { # fm <file> <key>  → valor do frontmatter YAML (escalares simples)
  awk -v k="$2" 'NR==1&&$0!="---"{exit} NR>1&&$0=="---"{exit} NR>1{ if (index($0,k":")==1){ s=substr($0,length(k)+2); gsub(/^[ \t]+|[ \t]+$/,"",s); gsub(/^"|"$/,"",s); print s; exit } }' "$1"
}
# specs canônicas = tudo em .specs/**/*.md exceto templates, README e postmortems (forense ≠ contrato)
list_specs() { find "$SPECS" -name '*.md' -not -path '*/_TEMPLATE/*' -not -name '_TEMPLATE.md' -not -name 'ADR-000-template.md' -not -name 'README.md' -not -path '*/postmortems/*' | sort; }
active_spec() { local f="$ROOT/.sdd/active-spec"; [ -f "$f" ] && grep -v '^#' "$f" | head -1 | tr -d '[:space:]' || true; }
