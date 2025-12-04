from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from datetime import datetime # datetimeをインポート

# --- アプリケーションの初期化 ---
app = Flask(__name__)
# config.py の Config クラスを読み込む
app.config.from_object('manga_relay.config.Config') 

# --- データベースの初期化 ---
db = SQLAlchemy(app)

# 重要な点: モデルとルートをインポートして、アプリケーションに認識させる
# このインポートにより、db.create_all()がComicとKomaモデルを見つけられる
from . import models
from . import views 

# --- グローバル設定の確認とフォルダ作成 ---
# UPLOAD_FOLDERが存在しなければ作成
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])