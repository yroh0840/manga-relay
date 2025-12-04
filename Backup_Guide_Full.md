# Git + ZIP ハイブリッドバックアップ完全版

## 1. 目的
このバックアップ方式は、**コードは GitHub（リモート）に安全に保存しつつ、コード外の資産（画像・動画・DB など）は ZIP で確実に保存**する方法です。

Git と ZIP の弱点を補完し合うため、個人開発でも最強レベルの耐障害性を実現できます。

---

## 2. バックアップ対象の考え方

### ◎ Git で保存すべきもの
- ソースコード
- HTML / CSS
- 設定ファイル
- requirements.txt など

### ◎ ZIP で保存すべきもの
- ユーザーアップロードファイル
- SQLite などの DB
- 大容量やバイナリ資産

---

## 3. 運用フロー

### A. Git 更新
```
git add .
git commit -m "update"
git push origin main
```

### B. ZIP バックアップ
```
python backup_zip.py
```

---

## 4. 自動 ZIP スクリプト

`backup_zip.py`:

```python
import os
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = PROJECT_DIR / "backups"
EXCLUDE = ["venv", "__pycache__", ".git", "node_modules", "backups"]

def should_exclude(path):
    return any(ex in str(path) for ex in EXCLUDE)

def zip_project():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    zip_name = BACKUP_DIR / f"backup_{timestamp}.zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
            for file in files:
                file_path = Path(root) / file
                if should_exclude(file_path):
                    continue
                z.write(file_path, file_path.relative_to(PROJECT_DIR))

    print(f"Backup created: {zip_name}")

if __name__ == "__main__":
    zip_project()
```

---

## 5. バックアップスクリプト

`backup.sh`:

```bash
#!/bin/bash
git add .
git commit -m "auto backup"
git push origin main
python3 backup_zip.py
echo "Backup complete!"
```

---

## 6. 復元手順

1. GitHub から clone  
2. venv を作り直す  
3. ZIP からユーザーデータを戻す  
4. 起動  

---

