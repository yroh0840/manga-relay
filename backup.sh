#!/bin/bash

# ========================
# backup.sh（安全版）
# 役割：
# ・今この瞬間のローカル状態をZIPで守る
# ・Git / ネットワーク / 外部状態に一切依存しない
# ・事故復旧専用（履歴は汚さない）
# ========================

BACKUP_DIR="./backups"
TS=$(date +"%Y%m%d_%H%M")
ZIP_PATH="$BACKUP_DIR/backup_${TS}.zip"

mkdir -p "$BACKUP_DIR"

zip -r "$ZIP_PATH" . \
  -x "venv/*" \
  -x ".git/*" \
  -x "backups/*"

echo "========================"
echo "Backup created:"
echo "  $ZIP_PATH"
echo "========================"
echo "※ Git 操作は行っていません（事故復旧専用）"
