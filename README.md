# 視聴リスト

映画・TV番組のウォッチリストを管理するためのDjangoウェブアプリケーションです。

## 主な機能

- ユーザー登録・ログイン・ログアウト
- 複数のウォッチリスト作成・編集・削除
- 映画・TV番組の追加・削除・編集
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

4. データベースのマイグレーションを実行します:
    ```bash
    python manage.py migrate
    ```

5. 開発サーバーを起動します:
    ```bash
    python manage.py runserver
    ```

6. ブラウザで `http://127.0.0.1:8000/` にアクセスして動作を確認してください。
