import os
import zipfile
from datetime import datetime

# プロジェクトルートを取得
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# バックアップフォルダ作成
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# ZIP ファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
zip_filename = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")

# ZIP に追加する対象（venv とバックアップフォルダは除外）
EXCLUDE_DIRS = {'manga-relay-venv', 'backups', '.git'}
EXCLUDE_FILES = {'.DS_Store'}

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        # 除外フォルダをスキップ
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES:
                continue
            filepath = os.path.join(root, file)
            # ZIP 内のパスはプロジェクトルートからの相対パスに
            arcname = os.path.relpath(filepath, path)
            ziph.write(filepath, arcname)

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipdir(BASE_DIR, zipf)

print(f"Backup created: {zip_filename}")
