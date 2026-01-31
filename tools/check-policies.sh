#!/usr/bin/env bash
# tools/check-policies.sh — Check files against project policies
# Usage: bash tools/check-policies.sh [file-or-directory]
# Checks: license compliance, disclosure language
set -euo pipefail

TARGET="${1:-.}"
ERRORS=0

echo "=== Policy Check: $TARGET ==="

# --- Disclosure language check ---
# Prohibited terms without hedge words (simplified grep-based check)
PROHIBITED_TERMS="fraud|corruption|embezzlement|money.laundering|criminal|guilty|illegal"
HEDGE_WORDS="potential|possible|alleged|signal|anomaly|red.flag|warrants.further|inconsistent.with|unusual.pattern"

echo ""
echo "--- Disclosure language check ---"

find_yaml_and_md() {
  find "$TARGET" -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.md" \) \
    ! -path "*/policies/*" \
    ! -path "*/_templates/*" \
    ! -path "*/schemas/*" \
    ! -path "*/.github/*" \
    ! -path "*/node_modules/*"
}

while IFS= read -r file; do
  # For each prohibited term, check if it appears without a nearby hedge word
  while IFS= read -r line_content; do
    line_lower=$(echo "$line_content" | tr '[:upper:]' '[:lower:]')
    if echo "$line_lower" | grep -qEi "$PROHIBITED_TERMS"; then
      if ! echo "$line_lower" | grep -qEi "$HEDGE_WORDS"; then
        echo "WARNING: $file — prohibited term without hedge word:"
        echo "  $line_content"
        ERRORS=$((ERRORS + 1))
      fi
    fi
  done < "$file"
done < <(find_yaml_and_md)

if [ $ERRORS -eq 0 ]; then
  echo "  All disclosure checks passed."
fi

# --- License check ---
echo ""
echo "--- License compliance check ---"

ALLOWED_LICENSES="CC0-1.0|CC-BY-4.0|CC-BY-SA-4.0|ODbL-1.0|PDDL-1.0|public-domain|government-open-data"
LICENSE_ERRORS=0

while IFS= read -r registry; do
  if ! command -v yq &> /dev/null; then
    echo "SKIP: yq not installed, cannot check licenses in $registry"
    continue
  fi
  LICENSES=$(yq '.datasets[].license' "$registry" 2>/dev/null || true)
  while IFS= read -r lic; do
    if [ -z "$lic" ] || [ "$lic" = "null" ]; then continue; fi
    if ! echo "$lic" | grep -qE "^($ALLOWED_LICENSES)$"; then
      echo "FAIL: $registry — disallowed license: $lic"
      LICENSE_ERRORS=$((LICENSE_ERRORS + 1))
    fi
  done <<< "$LICENSES"
done < <(find "$TARGET" -type f -name "registry.yml")

if [ $LICENSE_ERRORS -eq 0 ]; then
  echo "  All license checks passed."
fi
ERRORS=$((ERRORS + LICENSE_ERRORS))

# --- Large file check ---
echo ""
echo "--- Large file check (>1MB) ---"
LARGE_FILES=0
while IFS= read -r bigfile; do
  echo "FAIL: Large file detected: $bigfile"
  LARGE_FILES=$((LARGE_FILES + 1))
done < <(find "$TARGET" -type f -size +1M \
  ! -path "*/.git/*" \
  ! -path "*/node_modules/*" \
  ! -path "*/.venv/*")

if [ $LARGE_FILES -eq 0 ]; then
  echo "  No large files found."
fi
ERRORS=$((ERRORS + LARGE_FILES))

# --- Summary ---
echo ""
if [ $ERRORS -gt 0 ]; then
  echo "FAILED: $ERRORS policy violation(s) found."
  exit 1
else
  echo "PASSED: All policy checks passed."
fi
