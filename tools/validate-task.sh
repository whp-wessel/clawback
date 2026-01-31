#!/usr/bin/env bash
# tools/validate-task.sh — Validate a task YAML file against the task-spec schema
# Usage: bash tools/validate-task.sh <task-file.yml>
set -euo pipefail

SCHEMA="schemas/task-spec.schema.yml"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <task-file.yml>" >&2
  exit 1
fi

TASK_FILE="$1"

if [ ! -f "$TASK_FILE" ]; then
  echo "ERROR: File not found: $TASK_FILE" >&2
  exit 1
fi

if [ ! -f "$SCHEMA" ]; then
  echo "ERROR: Schema not found: $SCHEMA" >&2
  exit 1
fi

# Check for required tools
if ! command -v yq &> /dev/null; then
  echo "ERROR: yq (v4+) is required. Install: https://github.com/mikefarah/yq" >&2
  exit 1
fi

if ! command -v python3 &> /dev/null; then
  echo "ERROR: python3 is required." >&2
  exit 1
fi

# Convert YAML to JSON and validate against schema
TASK_JSON=$(yq -o=json "$TASK_FILE")
SCHEMA_JSON=$(yq -o=json "$SCHEMA")

python3 -c "
import json, sys
try:
    from jsonschema import validate, ValidationError
except ImportError:
    print('ERROR: pip install jsonschema', file=sys.stderr)
    sys.exit(1)

task = json.loads('''$TASK_JSON''')
schema = json.loads('''$SCHEMA_JSON''')

try:
    validate(instance=task, schema=schema)
    print('PASS: $TASK_FILE is valid.')
except ValidationError as e:
    print(f'FAIL: {e.message}', file=sys.stderr)
    print(f'  Path: {\" > \".join(str(p) for p in e.absolute_path)}', file=sys.stderr)
    sys.exit(1)
"
