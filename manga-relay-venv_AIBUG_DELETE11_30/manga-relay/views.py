from flask import render_template, request, redirect, url_for, send_from_directory
from sqlalchemy import func
import os
import uuid
# __init__ で定義された app と db をインポート
from . import app, db 
# models.py で定義されたモデルをインポート
from .models import Comic, Koma 


# --- ヘルパー関数 ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- ルート（静的ファイル） ---
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # アップロードフォルダからファイルを送信
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- ルート（表示） ---
@app.route('/')
def index():
    # Comicリストを取得し、テンプレートに渡す
    comics = Comic.query.order_by(Comic.started_at.desc()).all()
    return render_template('index.html', comics=comics) 


# --- ルート（投稿） ---
@app.route('/post', methods=['POST'])
def post_frame():
    file = request.files.get('file')
    comic_id_str = request.form.get('comic_id')
    
    if not file or file.filename == '' or not allowed_file(file.filename):
        return "不正なファイルです。", 400

    if comic_id_str == 'new' or not comic_id_str:
        # 新規漫画の作成
        new_comic = Comic()
        db.session.add(new_comic)
        db.session.commit()
        comic_id = new_comic.id
        new_frame_number = 1
        
    else:
        # 既存漫画への追加
        try:
            comic_id = int(comic_id_str)
        except ValueError:
            return "不正な漫画IDです。", 400
        
        # 既存のコマの最大 frame_number を取得
        max_frame = db.session.query(func.max(Koma.frame_number)).filter(
            Koma.comic_id == comic_id
        ).scalar()
        
        new_frame_number = (max_frame or 0) + 1


    # 4. ファイルの保存
    original_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = str(uuid.uuid4()) + '.' + original_ext
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(save_path)

    # 5. データベースに記録
    new_koma = Koma(
        comic_id=comic_id, 
        frame_number=new_frame_number,
        image_filename=unique_filename
    )
    
    db.session.add(new_koma)
    db.session.commit()
    
    return redirect(url_for('index'))