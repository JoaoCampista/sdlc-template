#!/usr/bin/env bash
# git hook prepare-commit-msg: anexa trailers Spec-Hash + Refs a partir de .sdd/active-spec (ou branch agent/F-*). Idempotente.
source "$(dirname "$0")/_lib.sh"
msg="$1"; src="${2:-}"; case "$src" in merge|squash) exit 0;; esac
id=$(active_spec); [ -z "$id" ] && id=$(git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -oE '(F|C)-[A-Za-z0-9_-]+' | head -1 || true)
[ -z "$id" ] && exit 0
spec=$(ls "$SPECS"/features/"$id"/spec.md "$SPECS"/components/"$id"/spec.md 2>/dev/null | head -1); [ -z "$spec" ] && exit 0
grep -q '^Spec-Hash:' "$msg" && exit 0
printf '\nSpec-Hash: sha256:%s\nRefs: %s\n' "$(sha "$spec")" "$id" >> "$msg"
