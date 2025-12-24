# ========================
# [メモ]
# backup.sh の役割
# 「今この瞬間のローカル状態を守る」
# バックアップは：
# ネットワークに依存しない
# 外部状態を信用しない
# 事故復旧用
# ========================

#!/bin/bash

# ========================
# 設定
# ========================
BACKUP_DIR="./backups"
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)

# ブランチ検出できない場合（コミットがない or Git管理外）
if [ -z "$BRANCH" ]; then
  echo "Git ブランチが存在しません。初回コミットを実施します。"
  git add .
  git commit -m "initial commit" || true
  BRANCH=$(git symbolic-ref --short HEAD)
fi

mkdir -p "$BACKUP_DIR"

# ========================
# ZIP 作成
# ========================
TS=$(date +"%Y%m%d_%H%M")
ZIP_PATH="$BACKUP_DIR/backup_${TS}.zip"

zip -r "$ZIP_PATH" . \
  -x "venv/*" \
  -x ".git/*" \
  -x "backups/*"

echo "Backup created: $ZIP_PATH"

# ========================
# Git 操作 (add → commit → push)
# ========================
git add .

git commit -m "auto backup" || echo "No changes to commit."

echo "Pushing to origin/$BRANCH ..."
git push origin "$BRANCH" || {
  echo "⚠ push に失敗しました。リモートに $BRANCH ブランチが存在しない可能性があります。"
  echo "リモートに作成するには:"
  echo "    git push -u origin $BRANCH"
}

echo "Backup complete!"
