#!/bin/bash
# 一键推送核心仓库 + 拆分 8 个 Cell 为独立仓库
# 用法: 在对话框输入  ! bash E:/ProjectHJM/forhacker/scripts/push-all.sh

set -e
cd "E:/ProjectHJM/forhacker"

echo "===== [1/9] 推送核心仓库 ====="
git remote add core https://github.com/HJSSSRX/core.git 2>/dev/null || true
git push -u core main
echo "核心仓库完成"

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

COUNT=1
for entry in "${CELLS[@]}"; do
  DIR="${entry%%:*}"
  NAME="${entry##*:}"
  COUNT=$((COUNT + 1))
  echo ""
  echo "===== [$COUNT/9] 拆分 $NAME ====="

  TMP="/tmp/forhacker-$DIR"
  rm -rf "$TMP"
  cp -r "cells/$DIR" "$TMP"
  mkdir -p "$TMP/.github/workflows"
  cp .github/workflows/quality.yml "$TMP/.github/workflows/"

  cd "$TMP"
  git init
  git checkout -b main
  git add .
  git commit -m "feat: $NAME Cell plugin for ForHacker" --quiet
  git remote add origin "https://github.com/HJSSSRX/plugin-$NAME.git"
  git push -u origin main --force
  echo "$NAME 完成"

  cd "E:/ProjectHJM/forhacker"
done

echo ""
echo "===== 全部完成 ====="
echo "验证: https://github.com/HJSSSRX?tab=repositories"
