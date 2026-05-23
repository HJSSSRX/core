#!/bin/bash
set -e
cd "E:/ProjectHJM/forhacker"

CELLS=(
  "forensics_core:forensics-core"
  "file_analyzer:file-analyzer"
  "log_parser:log-parser"
  "network_forensics:network-forensics"
  "registry_analyzer:registry-analyzer"
  "browser_forensics:browser-forensics"
  "email_forensics:email-forensics"
  "timeline_analyzer:timeline-analyzer"
)

for entry in "${CELLS[@]}"; do
  DIR="${entry%%:*}"
  NAME="${entry##*:}"
  echo "Updating $NAME ..."

  TMP="/tmp/forhacker-cell-$DIR"
  rm -rf "$TMP"
  cp -r "cells/$DIR" "$TMP"
  mkdir -p "$TMP/.github/workflows"
  cp .github/workflows/quality.yml "$TMP/.github/workflows/" 2>/dev/null || true

  pushd "$TMP" > /dev/null
  git init -q
  git checkout -b main -q
  git add .
  git commit -m "feat: Python 3.8 compat, applicable_extensions, YARA rules, tool fixes" --quiet
  git remote add origin "https://github.com/HJSSSRX/plugin-$NAME.git"
  git push -u origin main --force -q
  popd > /dev/null
  echo "  $NAME updated"
done

cd "E:/ProjectHJM/forhacker"
echo "All cells updated."
