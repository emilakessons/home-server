#!/bin/bash
set -euo pipefail

SUBJECT="${1:?Ange motiv, t.ex. \"paw patrol chase\"}"

curl -sS -X POST http://127.0.0.1:8787/print \
  -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"subject": sys.argv[1]}))' "$SUBJECT")"
echo
