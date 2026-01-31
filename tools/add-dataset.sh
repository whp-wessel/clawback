#!/usr/bin/env bash
# tools/add-dataset.sh — Register a new dataset in the repo
# Usage: bash tools/add-dataset.sh <dataset-id> <file-or-directory> [--jurisdiction <code>]
#
# This script:
#   1. Creates data/<dataset-id>/
#   2. Copies file(s) into it (Git LFS will track them)
#   3. Generates manifest.yml with SHA256 hashes
#   4. Prints a registry entry you can paste into the jurisdiction registry
#
# Example:
#   bash tools/add-dataset.sh nl-new-dataset /tmp/download.csv.gz --jurisdiction nl
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <dataset-id> <file-or-directory> [--jurisdiction <code>]" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  $0 nl-new-dataset /path/to/file.csv.gz --jurisdiction nl" >&2
  echo "  $0 eu-ted-2024 /path/to/directory/ --jurisdiction eu" >&2
  exit 1
fi

DATASET_ID="$1"
SOURCE="$2"
JURISDICTION=""

shift 2
while [ $# -gt 0 ]; do
  case "$1" in
    --jurisdiction) JURISDICTION="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Validate dataset ID
if ! echo "$DATASET_ID" | grep -qE '^[a-z0-9-]+$'; then
  echo "ERROR: Dataset ID must be lowercase alphanumeric with hyphens only." >&2
  exit 1
fi

DEST="data/$DATASET_ID"

if [ -d "$DEST" ]; then
  echo "WARNING: $DEST already exists. Files will be added to existing directory."
fi

mkdir -p "$DEST"

# Copy files
if [ -d "$SOURCE" ]; then
  echo "Copying directory contents..."
  cp -v "$SOURCE"/* "$DEST/" 2>/dev/null || true
elif [ -f "$SOURCE" ]; then
  echo "Copying file..."
  cp -v "$SOURCE" "$DEST/"
else
  echo "ERROR: $SOURCE is not a file or directory." >&2
  exit 1
fi

# Generate manifest
echo "Generating manifest.yml..."

MANIFEST="$DEST/manifest.yml"
cat > "$MANIFEST" << HEADER
# Dataset: $DATASET_ID
dataset_id: $DATASET_ID
name: ""
description: ""
source_url: ""
license: ""
jurisdiction: "$JURISDICTION"
access_date: "$(date +%Y-%m-%d)"

files:
HEADER

for f in "$DEST"/*; do
  [ -f "$f" ] || continue
  fname=$(basename "$f")
  [ "$fname" = "manifest.yml" ] && continue

  hash=$(shasum -a 256 "$f" | awk '{print $1}')
  size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)

  cat >> "$MANIFEST" << ENTRY
  - name: "$fname"
    sha256: "$hash"
    size_bytes: $size
    description: ""
ENTRY
done

echo ""
echo "=== Done ==="
echo "Created: $DEST/"
echo "Manifest: $MANIFEST"
echo ""
echo "Next steps:"
echo "  1. Edit $MANIFEST — fill in name, description, source_url, license"
echo "  2. Add a registry entry to jurisdictions/countries/$JURISDICTION/datasets/registry.yml"
echo "  3. git add data/$DATASET_ID/ && git commit"
echo ""

# Print a registry entry template
if [ -n "$JURISDICTION" ]; then
  echo "=== Registry entry template (paste into registry.yml) ==="
  echo ""
  echo "  - id: $DATASET_ID"
  echo "    name: \"\""
  echo "    source_url: \"\""
  echo "    license: \"\""
  echo "    format: csv"
  echo "    access_method: bulk-export"
  echo "    local_path: data/$DATASET_ID/"
  echo "    description: \"\""
  echo "    jurisdiction: $JURISDICTION"
  echo "    update_frequency: \"\""
  echo "    last_verified: \"$(date +%Y-%m-%d)\""
fi
