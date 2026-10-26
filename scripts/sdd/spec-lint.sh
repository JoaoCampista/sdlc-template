#!/usr/bin/env bash
set -e
exec python3 "$(dirname "$0")/sdd.py" lint "$@"
