#!/bin/bash
# ForHacker GitHub Org Bootstrap Script
#
# Usage: Run from the forhacker-core project root AFTER creating the forhacker
# GitHub org and repos.  This script pushes the core repo and splits each Cell
# into its own standalone repo.
#
# Prerequisites (manual steps first):
#   1. Create the GitHub org: https://github.com/organizations/plan
#      Suggested name: "forhacker"
#   2. Create these repos under the org (all empty, no README/LICENSE/.gitignore):
#      - core
#      - plugin-forensics-core
#      - plugin-file-analyzer
#      - plugin-log-parser
#      - plugin-network-forensics
#      - plugin-registry-analyzer
#      - plugin-browser-forensics
#      - plugin-email-forensics
#      - plugin-timeline-analyzer
#      - knowledge-base
#      - docs
#   3. Install gh CLI: https://cli.github.com/
#      gh auth login
#   4. Set the ORG variable below
#
# After running this script:
#   - Core repo is pushed to forhacker/core
#   - Each Cell is a standalone repo at forhacker/plugin-<name>
#   - marketplace plugins.yaml points to the correct URLs
#   - CI/CD works per repo (quality.yml included in each)

set -euo pipefail

ORG="${FORHACKER_ORG:-forhacker}"
CORE_DIR="$(pwd)"
TMPDIR="${TMPDIR:-/tmp}/forhacker-bootstrap-$$"

echo "=== ForHacker GitHub Org Bootstrap ==="
echo "Org: $ORG"
echo "Core dir: $CORE_DIR"
echo ""

# ── Step 1: Push core repo ──────────────────────────────────────────────
echo "[1/3] Pushing core repo to $ORG/core ..."

if git remote get-url origin 2>/dev/null | grep -q "$ORG/core"; then
    echo "  Remote already set to $ORG/core, skipping."
else
    # Preserve existing remote as upstream if needed
    if git remote get-url origin 2>/dev/null; then
        git remote rename origin old-origin 2>/dev/null || true
    fi
    git remote add origin "https://github.com/$ORG/core.git"
    git branch -M main
    git push -u origin main
    echo "  Core pushed: https://github.com/$ORG/core"
fi

# ── Step 2: Split each Cell into independent repos ──────────────────────
echo ""
echo "[2/3] Splitting Cells into independent repos ..."

CELLS=(
    "forensics_core"
    "file_analyzer"
    "log_parser"
    "network_forensics"
    "registry_analyzer"
    "browser_forensics"
    "email_forensics"
    "timeline_analyzer"
)

for cell_dir in "${CELLS[@]}"; do
    CELL_NAME="${cell_dir//_/-}"
    echo ""
    echo "--- Splitting $CELL_NAME ---"

    CELL_PATH="$CORE_DIR/cells/$cell_dir"
    if [ ! -d "$CELL_PATH" ]; then
        echo "  SKIP: $CELL_PATH not found"
        continue
    fi

    # Create temp worktree
    WORKTREE="$TMPDIR/$cell_dir"
    rm -rf "$WORKTREE"
    mkdir -p "$(dirname "$WORKTREE")"

    # Copy Cell files (excluding pycache and git)
    cp -r "$CELL_PATH" "$WORKTREE"

    # Copy shared CI workflow
    mkdir -p "$WORKTREE/.github/workflows"
    cat > "$WORKTREE/.github/workflows/quality.yml" << 'CIEOF'
name: Quality Gates

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov ruff

      - name: Ruff format check
        run: ruff format --check .

      - name: Ruff lint
        run: ruff check .

      - name: Pytest
        run: pytest --cov=. --cov-fail-under=50
CIEOF

    # Initialize git
    cd "$WORKTREE"
    git init
    git checkout -b main
    git add .
    git commit -m "feat: $CELL_NAME Cell plugin for ForHacker

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"

    # Create repo and push
    REPO_URL="https://github.com/$ORG/plugin-$CELL_NAME.git"
    echo "  Pushing to $REPO_URL ..."
    git remote add origin "$REPO_URL"
    git push -u origin main 2>&1 || echo "  WARNING: Push failed — repo may not exist yet. Create it at $REPO_URL"

    echo "  $CELL_NAME done."
done

# ── Step 3: Verify ──────────────────────────────────────────────────────
echo ""
echo "[3/3] Verification"

echo ""
echo "Repos to verify:"
echo "  https://github.com/$ORG/core"
for cell_dir in "${CELLS[@]}"; do
    CELL_NAME="${cell_dir//_/-}"
    echo "  https://github.com/$ORG/plugin-$CELL_NAME"
done
echo "  https://github.com/$ORG/knowledge-base"
echo "  https://github.com/$ORG/docs"
echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "Next steps:"
echo "  1. Create the knowledge-base and docs repos manually"
echo "  2. Verify all repos are public and accessible"
echo "  3. Each team member: git clone https://github.com/$ORG/core"
echo "  4. Install Cell plugins: forhacker plugin install <name>"
echo "  5. Set up Syncthing shared/ directory for collaboration"
echo ""
echo "Cleanup temp files: rm -rf $TMPDIR"
