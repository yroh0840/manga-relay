#!/usr/bin/env python3
"""
admin_delete.py

Usage examples:
  python admin_delete.py --koma 23
  python admin_delete.py --comic 10
  python admin_delete.py --koma 23 --hard --with-images --yes
  python admin_delete.py --comic 10 --hard --with-images --yes --db /path/to/comic_relay.sqlite --uploads /path/to/uploads

This script:
 - ensures a soft-delete column 'is_deleted' exists in table 'koma'
 - supports soft-delete (default) and hard-delete (--hard)
 - supports deleting single koma (--koma) or entire comic (--comic)
 - optionally deletes image files (--with-images)
 - backups the DB before destructive operations
 - resequences frame_number after hard-delete
 - runs VACUUM at the end (unless --no-vacuum)
"""
import argparse
import sqlite3
import os
import shutil
import sys
from datetime import datetime

def connect_db(db_path):
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def backup_db(db_path):
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    bak = f"{db_path}.bak.{ts}"
    shutil.copy2(db_path, bak)
    print(f"[backup] copied {db_path} -> {bak}")
    return bak

def ensure_is_deleted_column(conn):
    cur = conn.execute("PRAGMA table_info(koma)")
    cols = [r["name"] for r in cur.fetchall()]
    if "is_deleted" not in cols:
        print("[migrate] adding is_deleted column to koma (default 0)")
        conn.execute("ALTER TABLE koma ADD COLUMN is_deleted INTEGER DEFAULT 0")
        conn.commit()
    else:
        print("[migrate] is_deleted column already exists")

def get_koma_info(conn, koma_id):
    cur = conn.execute("SELECT id, comic_id, image_filename FROM koma WHERE id = ?", (koma_id,))
    return cur.fetchone()

def get_comic_komas(conn, comic_id):
    cur = conn.execute("SELECT id, image_filename FROM koma WHERE comic_id = ?", (comic_id,))
    return cur.fetchall()

def soft_delete_koma(conn, koma_id):
    info = get_koma_info(conn, koma_id)
    if not info:
        raise ValueError(f"koma id {koma_id} not found")
    conn.execute("UPDATE koma SET is_deleted = 1 WHERE id = ?", (koma_id,))
    conn.commit()
    print(f"[soft] koma {koma_id} marked is_deleted=1 (comic {info['comic_id']})")
    # soft-delete: do NOT resequence (keep frame slots; UI can show 'deleted' placeholder)
    return info["comic_id"]

def hard_delete_koma(conn, koma_id, uploads_dir=None, delete_image=False):
    info = get_koma_info(conn, koma_id)
    if not info:
        raise ValueError(f"koma id {koma_id} not found")
    comic_id = info["comic_id"]
    image = info["image_filename"]
    # delete the row
    conn.execute("DELETE FROM koma WHERE id = ?", (koma_id,))
    conn.commit()
    print(f"[hard] deleted koma {koma_id} from DB (comic {comic_id})")
    if delete_image and image:
        image_path = os.path.join(uploads_dir, image)
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"[file] removed image {image_path}")
        else:
            print(f"[file] image not found: {image_path}")
    # resequence frame_number for this comic
    resequence_comic(conn, comic_id)
    return comic_id

def soft_delete_comic(conn, comic_id):
    cur = conn.execute("SELECT COUNT(*) as c FROM comic WHERE id = ?", (comic_id,))
    if cur.fetchone()["c"] == 0:
        raise ValueError(f"comic id {comic_id} not found")
    conn.execute("UPDATE koma SET is_deleted = 1 WHERE comic_id = ?", (comic_id,))
    conn.commit()
    print(f"[soft] all komas in comic {comic_id} marked is_deleted=1")

def hard_delete_comic(conn, comic_id, uploads_dir=None, delete_images=False):
    # collect images
    rows = get_comic_komas(conn, comic_id)
    if not rows:
        print(f"[hard] No komas found for comic {comic_id} (still deleting comic row if exists)")
    # delete komas
    conn.execute("DELETE FROM koma WHERE comic_id = ?", (comic_id,))
    # delete comic
    conn.execute("DELETE FROM comic WHERE id = ?", (comic_id,))
    conn.commit()
    print(f"[hard] deleted all koma and comic {comic_id} from DB")
    if delete_images and uploads_dir:
        for r in rows:
            img = r["image_filename"]
            if img:
                p = os.path.join(uploads_dir, img)
                if os.path.exists(p):
                    os.remove(p)
                    print(f"[file] removed image {p}")
                else:
                    print(f"[file] not found: {p}")
    # no resequence across other comics needed
    return

def resequence_comic(conn, comic_id):
    print(f"[resequence] resequencing frame_number for comic {comic_id}")
    # uses a CTE to assign new numbers based on current order
    update_sql = """
    WITH sorted AS (
      SELECT id, ROW_NUMBER() OVER (ORDER BY frame_number) AS new_frame
      FROM koma
      WHERE comic_id = ?
    )
    UPDATE koma
    SET frame_number = (
      SELECT new_frame FROM sorted WHERE sorted.id = koma.id
    )
    WHERE comic_id = ?;
    """
    conn.execute(update_sql, (comic_id, comic_id))
    conn.commit()
    print("[resequence] done")

def run_vacuum(conn):
    print("[vacuum] running VACUUM")
    conn.execute("VACUUM;")
    conn.commit()
    print("[vacuum] done")

def parse_args():
    p = argparse.ArgumentParser(description="Admin delete utility for comic/koma (SQLite)")
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--koma", type=int, help="koma id to delete")
    target.add_argument("--comic", type=int, help="comic id to delete (all komas)")
    p.add_argument("--db", default="comic_relay.sqlite", help="path to sqlite db file")
    p.add_argument("--uploads", default="uploads", help="uploads directory path")
    p.add_argument("--hard", action="store_true", help="perform hard delete (DB row removal). Default = soft (is_deleted=1)")
    p.add_argument("--with-images", action="store_true", help="when hard deleting, also remove image files from uploads/")
    p.add_argument("--no-vacuum", action="store_true", help="do not run VACUUM at end")
    p.add_argument("--yes", action="store_true", help="auto-confirm destructive actions (required for --hard)")
    return p.parse_args()

def main():
    args = parse_args()
    db_path = args.db
    uploads_dir = args.uploads

    conn = connect_db(db_path)

    try:
        ensure_is_deleted_column(conn)

        # If hard requested but not confirmed, abort
        if args.hard and not args.yes:
            print("Hard delete requested -- must pass --yes to confirm. Aborting.")
            return

        # create DB backup before any destructive action (soft delete also backed up)
        backup_db(db_path)

        if args.koma:
            if args.hard:
                hard_delete_koma(conn, args.koma, uploads_dir=uploads_dir, delete_image=args.with_images)
            else:
                soft_delete_koma(conn, args.koma)
        elif args.comic:
            if args.hard:
                hard_delete_comic(conn, args.comic, uploads_dir=uploads_dir, delete_images=args.with_images)
            else:
                soft_delete_comic(conn, args.comic)

        if not args.no_vacuum:
            run_vacuum(conn)

        print("[done] operation completed successfully")

    except Exception as e:
        print("[ERROR]", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
