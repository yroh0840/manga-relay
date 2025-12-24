from . import db # パッケージ内の db インスタンスをインポート
from datetime import datetime
from sqlalchemy import func

# 1. 漫画リレー全体を管理する Comic モデル
class Comic(db.Model):
    __tablename__ = 'comic' # テーブル名を明示
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default='無題の漫画リレー')
    is_completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Komaとのリレーションシップを定義
    komas = db.relationship('Koma', backref='comic', lazy='dynamic') 

    def __repr__(self):
        return f'<Comic {self.id}: {self.title}>'


# 2. 個々のコマを管理する Koma モデル
class Koma(db.Model):
    __tablename__ = 'koma' # テーブル名を明示
    id = db.Column(db.Integer, primary_key=True)
    # 外部キー: comic.id を参照する
    comic_id = db.Column(db.Integer, db.ForeignKey('comic.id'), nullable=False)
    # コマの順番
    frame_number = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(120), unique=True, nullable=False)
    # 投稿日時
    posted_at = db.Column(db.DateTime, default=datetime.utcnow) 

    def __repr__(self):
        return f'<Koma {self.id} (Comic:{self.comic_id}, Seq:{self.frame_number})>'