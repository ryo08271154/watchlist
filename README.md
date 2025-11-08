# 視聴記録

映画・TV 番組のウォッチリストを管理するための Django 製ウェブアプリケーションです。

## 主な機能

- ユーザー登録・ログイン・ログアウト
- 複数のウォッチリスト作成・編集
- 映画・TV 番組の追加・編集
- 視聴状況（未視聴・視聴中・視聴済み）の管理
- 各コンテンツへの評価（星評価）とレビュー投稿
- 他ユーザーのレビュー閲覧
- 検索・フィルタリング機能

## セットアップ

1. リポジトリをクローンします:

   ```bash
   git clone https://github.com/ryo08271154/watchlist.git
   cd watchlist
   ```

2. 仮想環境を作成して有効化します:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. 依存関係をインストールします:

   ```bash
   pip install -r requirements.txt
   ```

4. `.env` ファイルを作成します。
   プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下の内容を追加します。

   ```
   SECRET_KEY='your_secret_key_here'
   DEBUG=False
   ALLOWED_HOSTS='*'
   DATABASE_URL=sqlite:///db.sqlite3
   ```

   `your_secret_key_here` は、Django の秘密鍵として使用するランダムな文字列に置き換えてください。

5. データベースのマイグレーションを実行します:

   ```bash
   python manage.py migrate
   ```

6. スーパーユーザーを作成します:
   管理画面にアクセスするためにスーパーユーザーを作成します。

   ```bash
   python manage.py createsuperuser
   ```

   プロンプトに従って、ユーザー名とパスワードを入力してください。

7. 開発サーバーを起動します:

   ```bash
   python manage.py runserver
   ```

8. ブラウザで `http://127.0.0.1:8000/` にアクセスして動作を確認してください。
