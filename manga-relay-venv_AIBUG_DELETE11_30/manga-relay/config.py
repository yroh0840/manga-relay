class Config:
    # SQLiteデータベースファイルのパス
    SQLALCHEMY_DATABASE_URI = 'sqlite:///comic_relay.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # アップロードフォルダの設定
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}