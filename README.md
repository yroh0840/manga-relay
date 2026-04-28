# 🎨 MANGA RELAY（漫画リレー）

複数人で1コマずつ投稿し、1つの漫画をつくるWebサービスです。  
画像投稿を通じて、予測できないストーリーが連鎖していく体験を提供します。

---

## 🚀 Demo
https://manga-relay-1.onrender.com

※ Render無料プランのため、初回アクセス時に約20秒の起動時間があります（コールドスタート）。

---

## 📸 主な機能

- 漫画リレーの作成
- 画像（コマ）の投稿
- コマの順番表示
- 管理画面（Basic認証）
- コメント投稿機能
- Cloudinaryによる画像管理

---

## 🛠️ 技術構成

- Backend: Flask（Python）
- Database: PostgreSQL（Render）
- Hosting: Render（Free Plan）
- ORM: SQLAlchemy
- Migration: Flask-Migrate
- 画像管理: Cloudinary

---

## 🔧 工夫した点・取り組み

- Heroku環境からRenderへの移行を実施
- PostgreSQLのバックアップ（pg_dump）と復元（pg_restore）を用いたデータ移行
- pg_restoreのバージョン差異エラーを解決し、正常に復元
- Cloudinaryを利用して画像ストレージを外部化

---

## ⚠️ 補足

- 無料プランのためコールドスタートあり（約20秒）
- 常時起動は有料プランで解消可能

---

## 📌 今後の改善

- UI/UXの改善
- ページ表示速度の最適化
- ユーザー認証機能の追加
- 通知機能の強化

---