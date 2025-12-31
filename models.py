# from datetime import datetime
# from app import db  # すでにある db を使う

# class AdminDM(db.Model):
#     __tablename__ = "admin_dm"

#     id = db.Column(db.Integer, primary_key=True)
#     category = db.Column(db.String(50))  # 要望 / 不具合 / クレーム / その他
#     message = db.Column(db.Text, nullable=False)
#     wants_reply = db.Column(db.Boolean, default=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)