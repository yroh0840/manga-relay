# 🎨 MANGA RELAY（漫画リレー）

複数人で1コマずつ投稿し、1つの漫画をつくるWebサービスです。  
ユーザーの投稿によってストーリーが連鎖的に変化していく体験を提供します。

---

## 🚀 Demo
https://manga-relay-1.onrender.com

※ Render無料プランのため、初回アクセス時に約40秒の起動時間があります（コールドスタート）。

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
- PostgreSQLのバックアップ（pg_dump）と復元（pg_restore）によるデータ移行
- pg_restoreのバージョン差異エラーを解決し、本番環境へ復元
- Cloudinaryを利用して画像ストレージを外部化し、運用を考慮した構成にした

---

## ⚠️ 補足

- 本サービスは現在開発・検証段階のプロジェクトです
- テスト投稿データが含まれています
- 無料プランのためコールドスタートあり（約40秒）
- 常時起動は有料プランで解消可能

---

## 📌 今後の改善

- UI/UXの改善
- ページ表示速度の最適化
- ユーザー認証機能の追加
- 投稿品質のコントロール機能
- 通知機能の強化