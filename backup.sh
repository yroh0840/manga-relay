#!/bin/bash

# --- Git による自動コミット & push ---
git add .

# 変更がある場合のみコミット
if ! git diff-index --quiet HEAD --; then
    git commit -m "auto backup"
fi

# main ブランチに push（初回 push の場合 -u オプション）
git push -u origin main

# --- ZIP バックアップ作成 ---
python3 backup_zip.py

echo "Backup complete!"
