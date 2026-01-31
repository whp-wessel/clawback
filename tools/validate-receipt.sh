#!/usr/bin/env bash
# tools/validate-receipt.sh — Validate a run receipt against the run-receipt schema
# Usage: bash tools/validate-receipt.sh <receipt-file.yml>
set -euo pipefail

SCHEMA="schemas/run-receipt.schema.yml"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <receipt-file.yml>" >&2
  exit 1
fi

RECEIPT_FILE="$1"

if [ ! -f "$RECEIPT_FILE" ]; then
  echo "ERROR: File not found: $RECEIPT_FILE" >&2
  exit 1
fi

if [ ! -f "$SCHEMA" ]; then
  echo "ERROR: Schema not found: $SCHEMA" >&2
  exit 1
fi

if ! command -v yq &> /dev/null; then
  echo "ERROR: yq (v4+) is required." >&2
  exit 1
fi

if ! command -v python3 &> /dev/null; then
  echo "ERROR: python3 is required." >&2
  exit 1
fi

RECEIPT_JSON=$(yq -o=json "$RECEIPT_FILE")
SCHEMA_JSON=$(yq -o=json "$SCHEMA")

python3 -c "
import json, sys
try:
    from jsonschema import validate, ValidationError
except ImportError:
    print('ERROR: pip install jsonschema', file=sys.stderr)
    sys.exit(1)

receipt = json.loads('''$RECEIPT_JSON''')
schema = json.loads('''$SCHEMA_JSON''')

try:
    validate(instance=receipt, schema=schema)
    print('PASS: $RECEIPT_FILE is valid.')
except ValidationError as e:
    print(f'FAIL: {e.message}', file=sys.stderr)
    print(f'  Path: {\" > \".join(str(p) for p in e.absolute_path)}', file=sys.stderr)
    sys.exit(1)
"
