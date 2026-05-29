# FastAPI + SQLite + Alembic 統合ガイド

## 概要

このプロジェクトは、FastAPI に SQLite データベースと Alembic マイグレーション管理を統合しました。以下の機能が実装されています：

### 実装内容

#### 1. テーブル構成（2つ）

**projects テーブル**
- プロジェクト管理用のテーブル
- カラム：id, projectKey, name, chartEnabled, useResolvedForChart, subtaskingEnabled など
- APIのレスポンス形式に合わせた設計

**issues テーブル**
- 課題管理用のテーブル
- カラム：id, projectId(FK), issueKey, keyId, issueTypeId, summary, description, priorityId, statusId など
- プロジェクトと1:多の関係

#### 2. ファイル構成

```
.
├── main.py                 # FastAPIアプリケーション
├── database.py             # DB接続設定
├── models.py               # SQLAlchemyモデル定義
├── pyproject.toml          # 依存関係設定
├── alembic.ini             # Alembic設定ファイル
└── migrations/
    ├── env.py              # マイグレーション実行環境
    ├── script.py.mako      # マイグレーションテンプレート
    └── versions/           # マイグレーション履歴
        └── 224cd03114a0_initial_migration...py
```

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
pip install fastapi uvicorn sqlalchemy alembic python-multipart
```

### 2. Alembicの初期化（※すでに完了）

```bash
alembic init migrations
```

### 3. マイグレーション設定

**alembic.ini** で以下を設定（※すでに完了）：
```ini
sqlalchemy.url = sqlite:///./backlog.db
```

**migrations/env.py** で以下を設定（※すでに完了）：
```python
from models import Base
target_metadata = Base.metadata
```

### 4. マイグレーション生成と実行

#### 初期マイグレーション（すでに実行済み）
```bash
alembic revision --autogenerate -m "Initial migration: create projects and issues tables"
```

#### マイグレーション適用（すでに実行済み）
```bash
alembic upgrade head
```

## マイグレーション管理

### 新しいモデル追加時

1. [models.py](models.py) にモデルを追加
2. マイグレーション生成：
   ```bash
   alembic revision --autogenerate -m "説明"
   ```
3. マイグレーション適用：
   ```bash
   alembic upgrade head
   ```

### マイグレーション履歴確認

```bash
alembic history
```

### マイグレーションのロールバック

最後のマイグレーションに戻す：
```bash
alembic downgrade -1
```

## APIエンドポイント

### プロジェクト作成
**POST** `/api/v2/projects?apiKey=valid_api_key_12345`

```bash
curl -X POST "http://127.0.0.1:8001/api/v2/projects?apiKey=valid_api_key_12345" \
  -d "name=テストプロジェクト" \
  -d "key=TEST_PRJ" \
  -d "chartEnabled=true" \
  -d "useWiki=true"
```

レスポンス：
```json
{
  "id": 1,
  "projectKey": "TEST_PRJ",
  "name": "テストプロジェクト",
  "chartEnabled": true,
  ...
}
```

### 課題作成
**POST** `/api/v2/issues?apiKey=valid_api_key_12345`

```bash
curl -X POST "http://127.0.0.1:8001/api/v2/issues?apiKey=valid_api_key_12345" \
  -d "projectId=1" \
  -d "summary=テスト課題" \
  -d "issueTypeId=1" \
  -d "priorityId=2" \
  -d "description=これはテスト課題です"
```

レスポンス：
```json
{
  "id": 1,
  "projectId": 1,
  "issueKey": "TEST_PRJ-1",
  "keyId": 1,
  ...
}
```

## サーバー起動

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

## DB確認

SQLite DBファイルは `backlog.db` に保存されます。

```bash
sqlite3 backlog.db
> .tables
> SELECT * FROM projects;
> SELECT * FROM issues;
```

## 主な実装

### [database.py](database.py)
- SQLite接続設定
- セッション管理
- 依存関係注入用の `get_db()` 関数

### [models.py](models.py)
- `Project` モデル：プロジェクト情報
- `Issue` モデル：課題情報
- `to_dict()` メソッド：APIレスポンス用変換

### [main.py](main.py)
- 更新：DBへの保存処理
- プロジェクト名の重複チェック
- 課題のissueKey自動生成

## ポイント

1. **自動ID生成**：keyId はプロジェクト内で自動連番生成
2. **外部キー制約**：issues.projectId は projects.id を参照
3. **タイムスタンプ**：created, updated は自動入力
4. **Alembic管理**：スキーマ変更は Alembic で管理、SQL直接編集不要
