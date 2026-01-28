

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc 
from sqlalchemy.pool import NullPool 
import os 
import uuid
from datetime import datetime
from flask_migrate import Migrate
from functools import wraps # Basic認証用 
from flask import Response # Basic認証用 
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests

cloudinary.config(secure=True)
# app.py の先頭に追加して実行
# print("RUNNING FILE:", os.path.abspath(__file__))


# --- アプリケーションの初期化 ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# ★★★ DBパス設定の絶対パス化 ★★★
basedir = os.path.abspath(os.path.dirname(__file__))
app.instance_path = basedir 

# 1. DB.sqlite接続設定
# db_filename = 'comic_relay.sqlite'
# db_path = os.path.join(basedir, db_filename)

# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}' 
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB.postgres設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 2. アップロードフォルダの設定
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
# sqlite用であり、postgresには使えないエラーになる
# app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
#     "connect_args": {
#         "check_same_thread": False
#     },
#     "poolclass": NullPool,
# }
app.config['DEBUG'] = False

# 環境変数
# 受け入れる画像の拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# basic認証で管理画面を開く--
ADMIN_USER = os.environ.get("ADMIN_USER") 
ADMIN_PASS = os.environ.get("ADMIN_PASS")
# -----------------------
# --- データベースの初期化 ---
db = SQLAlchemy(app)
# from models import AdminDM

# --- フォルダの作成 ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

migrate = Migrate(app, db)

# ====================================================================
# --- データベースモデル ---
# ====================================================================
class Comic(db.Model):
    __tablename__ = 'comic'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default='無題の漫画リレー')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Integer, default=0, nullable=False)
    max_koma = db.Column(db.Integer, default=20)
    komas = db.relationship('Koma', backref='comic', lazy='dynamic') 


    def __repr__(self):
        return f'<Comic {self.id}: {self.title}>'

class Koma(db.Model):
    __tablename__ = 'koma'
    id = db.Column(db.Integer, primary_key=True)
    comic_id = db.Column(db.Integer, db.ForeignKey('comic.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(120), unique=True, nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow) 
    is_deleted = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Koma {self.id} (Comic:{self.comic_id}, Seq:{self.frame_number})>'

class AdminDM(db.Model):
    __tablename__ = 'admin_dm'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))  # 要望 / 不具合 / クレーム / その他
    message = db.Column(db.Text, nullable=False)
    wants_reply = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PublicComment(db.Model):
    __tablename__ = "public_comment"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_public = db.Column(db.Boolean, default=True)  # 公開 or 非公開
    # 管理者からの一言返信（任意）
    admin_reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# herokuでは不要
# with app.app_context():
#     # 接続を取得して PRAGMA を実行
#     with db.engine.connect() as conn:
#         conn.execute(db.text('PRAGMA journal_mode=WAL;'))
#         conn.execute(db.text('PRAGMA synchronous=NORMAL;'))


# LINEメッセージ送信用の関数
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")

def send_line_notify(message):
    if not LINE_TOKEN or not LINE_GROUP_ID:
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_GROUP_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }

    requests.post(url, headers=headers, json=payload)


@app.route("/line/webhook", methods=["POST"])
def line_webhook():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        source = event.get("source", {})
        if source.get("type") == "group":
            group_id = source.get("groupId")
            print("GROUP_ID:", group_id)

    return "OK"


# ====================================================================
# --- ヘルパー関数とルート ---
# ====================================================================
# basic認証用
def basic_auth_required(username, password):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth = request.authorization
            if not auth or auth.username != username or auth.password != password:
                return Response(
                    "Unauthorized", 401,
                    {"WWW-Authenticate": 'Basic realm="Admin Area"'}
                )
            return f(*args, **kwargs)
        return wrapped
    return decorator


def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 


# 管理ページ
@app.route('/admin/list')
@basic_auth_required(ADMIN_USER, ADMIN_PASS) # basic認証 これでURLを知っていてもユーザー名とパスが必要
def admin_list():
    comics = Comic.query.order_by(Comic.started_at.desc()).all()
    return render_template("admin_list.html", comics=comics, Koma=Koma)


# for_url()で画像表示しているため不要となった-------
# @app.route('/uploads/<path:filename>')
# def uploaded_file(filename):
#   return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
# ---------------------------------------------

@app.route('/admin/comic/<int:comic_id>')
@basic_auth_required(ADMIN_USER, ADMIN_PASS)
def admin_comic_detail(comic_id):
    # Comic と関連する Koma を取得
    comic = Comic.query.get_or_404(comic_id)
    return render_template('admin_comic_detail.html', comic=comic, Koma=Koma)



# 削除-----------
@app.route('/admin/delete/comic/<int:comic_id>', methods=['POST'])
@basic_auth_required(ADMIN_USER, ADMIN_PASS)
def delete_comic(comic_id):
    comic = Comic.query.get_or_404(comic_id)
    # コミックの is_deleted を ON にする
    comic.is_deleted = 1
    # 関連するコマも全部削除
    for koma in comic.komas:
        koma.is_deleted = 1
    db.session.commit()
    # flash(f'コミック "{comic.title}" をソフトデリートしました。', 'success')
    return redirect(url_for('admin_list'))

@app.route('/admin/delete/koma/<int:koma_id>', methods=['POST'])
@basic_auth_required(ADMIN_USER, ADMIN_PASS)
def delete_koma(koma_id):
    koma = Koma.query.get_or_404(koma_id)
    koma.is_deleted = 1
    db.session.commit()
    # flash(f'コマ {koma.frame_number} を削除（ソフトデリート）しました。', 'success')
    return redirect(url_for('admin_list'))

# ----------

@app.route("/dm", methods=["GET", "POST"])
def admin_dm():
    if request.method == "POST":
        category = request.form.get("category")
        message = request.form.get("message")
        wants_reply = True if request.form.get("wants_reply") else False

        if not message:
            flash("内容を入力してください", "error")
            return redirect(url_for("admin_dm"))

        dm = AdminDM(
            category=category,
            message=message,
            wants_reply=wants_reply
        )
        db.session.add(dm)
        db.session.commit()

        flash("送信しました。ありがとう！", "success")
        return redirect(url_for("admin_dm"))

    return render_template("admin_dm.html", hide_dm_link=True)


# --- index ルート (一覧表示と投稿フォーム) ---
@app.route('/')
def index():
    comics = Comic.query.filter_by(is_deleted=0).order_by(Comic.started_at.desc()).all()
    
    for comic in comics:
        comic.koma_count = Koma.query.filter_by(
            comic_id=comic.id,
            is_deleted=0
        ).count()
    
    return render_template('index.html', comics=comics, db=db, Koma=Koma)
# 
# --- post ルート (コマの投稿処理) ---
@app.route('/post', methods=['POST'])
def post_frame():
    title = request.form.get('title') or '無題の漫画リレー'
    max_koma = request.form.get("max_koma", type=int)

    # 念のための保険
    if max_koma is None:
        max_koma = 20

    file = request.files.get('file')
    comic_id_str = request.form.get('comic_id')

    try: 
        if not file or file.filename == '':
            return redirect(request.referrer or url_for('index'))

        if not allowed_file(file.filename):
            return '許可されていないファイル形式です', 400
        
        comic_id = None
        new_frame_number = 1
        
        # 新規リレー
        if comic_id_str == 'new' or not comic_id_str:
            comic = Comic(title=title, max_koma=max_koma)
            db.session.add(comic)
            db.session.flush()
            comic_id = comic.id
        else:
            comic_id = int(comic_id_str)
            comic = db.session.get(Comic, comic_id)
            if not comic:
                return "存在しない漫画IDです。", 404

            max_frame = db.session.query(func.max(Koma.frame_number)).filter(
                Koma.comic_id == comic_id
            ).scalar()
            new_frame_number = (max_frame or 0) + 1

        # ファイル保存
        # ext = file.filename.rsplit('.', 1)[1].lower()
        # filename = str(uuid.uuid4()) + '.' + ext
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # 保存パスもUUIDも不要になる
        # result = cloudinary.uploader.upload(file)
        # cloudinaryのフォルダ構成を見やすく整理して保存
        send_line_notify(
            f"🖊 新しいコマが投稿されたよ！\n"
            f"{request.url_root}comic/{comic_id}"
        )


        result = cloudinary.uploader.upload(file, folder=f"manga_relay/{comic_id}")
        image_url = result["secure_url"]

        # DB 追加
        new_koma = Koma(
            comic_id=comic_id,
            frame_number=new_frame_number,
            image_filename=image_url
        )
        db.session.add(new_koma)
        db.session.commit()

        # ★★ 投稿元に戻る ★★
        ref = request.referrer or ""
        if f"/comic/{comic_id}" in ref:
            return redirect(url_for('comic_detail', comic_id=comic_id))

        return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error: {e}")
        return "サーバーエラー", 500

    finally:
        db.session.remove()

# フッターに配置する公開用コメント
@app.route("/footer-comment", methods=["POST"])
def footer_comment():
    message = request.form.get("message")
    is_public = True if request.form.get("is_public") else False

    if not message:
        flash("内容を入力してください", "error")
        return redirect(request.referrer or url_for("index"))

    comment = PublicComment(
        message=message,
        is_public=is_public
    )
    db.session.add(comment)
    db.session.commit()

    flash("送信しました。ありがとう！", "success")
    return redirect(request.referrer or url_for("index"))
# すべてのテンプレートのbase.html用に一括できる
@app.context_processor
def inject_public_comments():
    comments = (
        PublicComment.query
        .filter_by(is_public=True)
        .order_by(PublicComment.created_at.desc())
        .limit(5)
        .all()
    )
    return dict(public_comments=comments)



# コミックのコマのページ
@app.route('/comic/<int:comic_id>')
def comic_detail(comic_id):
    comic = Comic.query.get_or_404(comic_id)

    komas = comic.komas.filter_by(
        is_deleted=0
    ).order_by(Koma.frame_number.asc()).all()

    koma_count = len(komas) # コマの数

    return render_template(
        'comic_detail.html', 
        comic=comic, 
        komas=komas,
        koma_count=koma_count
    )

if __name__ == '__main__':
  # debug=False, threaded=Falseを維持
    with app.app_context():
        db.create_all()
    app.run(threaded=False)

