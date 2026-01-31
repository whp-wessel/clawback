#!/usr/bin/env bash
# tools/setup.sh — One-time setup for new contributors (humans and agents)
# Run from the repo root: bash tools/setup.sh
set -euo pipefail

echo "=== ClawBack contributor setup ==="

# 1. Check git-lfs
if ! command -v git-lfs &>/dev/null; then
  echo "Installing git-lfs..."
  if command -v brew &>/dev/null; then
    brew install git-lfs
  elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y git-lfs
  else
    echo "ERROR: Install git-lfs manually: https://git-lfs.com"
    exit 1
  fi
fi
git lfs install

# 2. Configure LFS credentials
echo "Configuring LFS server credentials..."
git config credential.http://168.119.100.15.helper store
printf "protocol=http\nhost=168.119.100.15\nusername=clawback\npassword=DfZ2G5yKBVTfZESaqcOKNoDc7g3cDuRa\n" | git credential approve

# 3. Pull LFS objects (if not already downloaded)
echo "Fetching LFS data..."
git lfs pull

# 4. Verify
LFS_COUNT=$(git lfs ls-files | wc -l | tr -d ' ')
DATA_DIRS=$(ls -d data/*/ 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "=== Setup complete ==="
echo "LFS objects: $LFS_COUNT"
echo "Dataset directories: $DATA_DIRS"
echo ""
echo "Next steps:"
echo "  1. Read CLAUDE.md for the full workflow"
echo "  2. Pick a task from tasks/ai/ (status: open)"
echo "  3. Create a branch: git checkout -b task/{task-id}"
echo "  4. Do the work, commit, push, open a PR"
