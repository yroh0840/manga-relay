from manga-relay import app

if __name__ == '__main__':
    # 外部からアクセスできるよう host='0.0.0.0' を追加 (開発環境用)
    app.run(debug=True, host='0.0.0.0')