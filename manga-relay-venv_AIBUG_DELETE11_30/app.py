from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# ---- DB 設定 ----
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ---- モデル定義 ----
class Comic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    # Comic → Koma のリレーション
    komas = db.relationship('Koma', backref='comic', lazy='dynamic')


class Koma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comic_id = db.Column(db.Integer, db.ForeignKey('comic.id'))
    image_path = db.Column(db.String(500))
    is_deleted = db.Column(db.Boolean, default=False)


# ---- 画像配信用 ----
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('static/uploads', filename)


# ---- 管理画面 メニュー ----
@app.route('/admin_list')
def admin_list():
    return render_template("admin_list.html")


# ---- A（縦リスト） ----
@app.route('/admin_list/a')
def admin_list_a():
    comics = Comic.query.order_by(Comic.id.desc()).all()
    return render_template("admin_list_a.html", comics=comics)


# ---- B（カードグリッド） ----
@app.route('/admin_list/b')
def admin_list_b():
    comics = Comic.query.order_by(Comic.id.desc()).all()
    return render_template("admin_list_b.html", comics=comics)


# ---- C（2カラム UI） ----
@app.route('/admin_list/c')
def admin_list_c():
    comics = Comic.query.order_by(Comic.id.desc()).all()
    return render_template("admin_list_c.html", comics=comics)


# ---- Comic のソフト削除 ----
@app.route('/admin_soft_delete_comic/<int:comic_id>', methods=['POST'])
def admin_soft_delete_comic(comic_id):
    comic = Comic.query.get_or_404(comic_id)

    if not comic.is_deleted:
        comic.is_deleted = True

        # 配下の Koma も全部ソフト削除
        for koma in comic.komas.all():
            koma.is_deleted = True

        db.session.commit()

    return redirect(request.referrer or url_for('admin_list'))


# ---- Comic の削除解除(復元) ----
@app.route('/admin_restore_comic/<int:comic_id>', methods=['POST'])
def admin_restore_comic(comic_id):
    comic = Comic.query.get_or_404(comic_id)

    if comic.is_deleted:
        comic.is_deleted = False

        # Koma も一緒に復元
        for koma in comic.komas.all():
            koma.is_deleted = False

        db.session.commit()

    return redirect(request.referrer or url_for('admin_list'))


# ---- Koma の単体ソフト削除 ----
@app.route('/admin_soft_delete_koma/<int:koma_id>', methods=['POST'])
def admin_soft_delete_koma(koma_id):
    koma = Koma.query.get_or_404(koma_id)

    koma.is_deleted = True
    db.session.commit()

    return redirect(request.referrer or url_for('admin_list'))


# ---- Koma の削除解除（復元） ----
@app.route('/admin_restore_koma/<int:koma_id>', methods=['POST'])
def admin_restore_koma(koma_id):
    koma = Koma.query.get_or_404(koma_id)

    koma.is_deleted = False
    db.session.commit()

    return redirect(request.referrer or url_for('admin_list'))


# ---- 起動 ----
if __name__ == "__main__":
    # 初回は DB 作成
    with app.app_context():
        db.create_all()

    app.run(debug=True)
