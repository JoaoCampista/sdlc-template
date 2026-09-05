#!/usr/bin/env bash
# Lint R1–R5 de uma spec. Uso: spec-lint.sh <arquivo.md> [...]. Exit 1 em erro; avisos não bloqueiam.
source "$(dirname "$0")/_lib.sh"
rc=0
for f in "$@"; do
  [ -f "$f" ] || { echo "ERRO: não existe: $f"; rc=1; continue; }
  case "$f" in */_TEMPLATE/*|*_TEMPLATE.md|*ADR-000-template.md|*README.md) continue;; esac
  id=$(fm "$f" id); kind=$(fm "$f" kind); status=$(fm "$f" status)
  err() { echo "ERRO [$1] $f: $2"; rc=1; }; warn() { echo "AVISO [$1] $f: $2"; }
  head -1 "$f" | grep -q '^---$' || err R1 "sem frontmatter"
  for k in id kind title parent version status last_updated; do [ -n "$(fm "$f" $k)" ] || err R1 "frontmatter sem '$k'"; done
  echo "$id" | grep -Eq '^(F|C|PROD|CONST|ADR|PLAN|TASKS|RISK|PM|DS)-[A-Za-z0-9]+([-_][A-Za-z0-9]+)*(-v[0-9]+)?$' || err R1 "id inválido: '$id'"
  ph=$(grep -oE '<[^<>]*( |:|…|YYYY|DOMINIO|NOME|Título|Tema|slug|path|time|nomes?|papel|ação|valor|explícito|contrato|alternativa|delta|link|lição|escopo|data|descrição|kind|erro)[^<>]*>' "$f" | sort -u | head -3 | tr '\n' ' '); [ -n "$ph" ] && err R1 "placeholders de template ainda presentes: $ph"
  case "$kind" in
    feature_spec|component_spec)
      for s in '## WHAT/HOW' '## User Stories' '## Acceptance Criteria' '## NFRs' '## NEEDS_CLARIFICATION'; do grep -qF "$s" "$f" || err R2 "falta seção literal '$s'"; done
      acs=$(grep -cE '^- \*\*AC-[0-9]+[a-z]?\.\*\*' "$f" || true); [ "$acs" -ge 1 ] || err R3 "nenhuma AC no formato '- **AC-N.** …'"
      grep -E '^- \*\*AC-[0-9]+[a-z]?\.\*\*' "$f" | grep -vq '@test:' && err R3 "há AC sem '@test:<path>'"
      while read -r p; do [ -z "$p" ] && continue
        if [ ! -e "$ROOT/$p" ]; then [ "$status" = approved ] && err R5 "@test não existe: $p" || warn R5 "@test ainda não existe: $p"; fi
      done < <(grep -oE '@test:[^ )]+' "$f" | cut -d: -f2 | sort -u)
      if [ "$status" = approved ]; then
        awk '/^## NEEDS_CLARIFICATION/{f=1;next} /^## /{f=0} f' "$f" | grep -vE '^[[:space:]]*$|^- ?(nenhum|none)' | grep -q . && err R4 "NEEDS_CLARIFICATION aberto em spec approved"
      fi;;
    adr)
      for s in '## Contexto' '## Decisão' '## Consequências' '## Alternativas consideradas' '## Riscos' '## Fences contra regressão' '## Revisões'; do grep -qF "$s" "$f" || err R2 "ADR sem seção '$s'"; done
      echo "$status" | grep -Eq '^(in_review|accepted|superseded|deprecated)$' || err R1 "status de ADR inválido: $status";;
    design_system_spec)
      for sec in '## Escopo' '## Regras' '## Enforcement' '## Exemplos canônicos' '## Anti-padrões' '## Changelog'; do grep -qF "$sec" "$f" || err R2 "DS sem seção '$sec'"; done
      grep -qE '^\| R[0-9]+ \|' "$f" || err R2 "DS sem linha de enforcement (| R1 | como | onde |) — regra sem enforcement é folclore"
      for rid in $(grep -oE '^[0-9]+\. \*\*R[0-9]+' "$f" | grep -oE 'R[0-9]+'); do grep -qE "^\| $rid \|" "$f" || err R2 "regra $rid sem linha em ## Enforcement — regra sem enforcement é folclore"; done;;
    postmortem)
      for s in '## §1' '## §2' '## §3' '## §4' '## §5' '## §6' '## §7'; do grep -qF "$s" "$f" || err R2 "postmortem sem '$s'"; done
      grep -q 'Spec gap identificado' "$f" || warn R2 "postmortem sem 'Spec gap identificado'";;
  esac
done
[ $rc -eq 0 ] && echo "spec-lint: OK"; exit $rc
