# EC2へのFastAPI + PostgreSQL デプロイメントガイド

## 目次
1. [推奨EC2インスタンススペック](#推奨ec2インスタンススペック)
2. [EC2インスタンスの初期セットアップ](#ec2インスタンスの初期セットアップ)
2. [Python、PostgreSQL、uvのインストール](#pythonpostgresqluvのインストール)
3. [FastAPIアプリケーションのセットアップ](#fastapiアプリケーションのセットアップ)
4. [ローカルからPostgresへのアクセス](#ローカルからpostgresへのアクセス)

---

## 推奨EC2インスタンススペック

### 一人確認用（開発・テスト環境）

| 項目 | スペック | 理由 |
|------|--------|------|
| **インスタンスタイプ** | t2.micro または t3.micro | 低コスト、バーストキャパシティ対応 |
| **vCPU** | 1 | FastAPI + PostgreSQLで十分 |
| **メモリ** | 1GB | 軽微な処理のみなら対応可能 |
| **ストレージ** | 20GB EBS（gp3） | OS + PostgreSQL + アプリケーション用 |
| **OS** | Ubuntu 22.04 LTS | サポート期間が長い |
| **月額コスト** | $8～15（AWS無料枠対象外の場合） | t2.micro/t3.microの低コスト |

### スペック詳細

#### 推奨の理由

**t2.micro / t3.micro の利点：**
- CPU クレジット機能により、バースト可能
- 低トラフィック環境に最適
- コスト効率が高い
- 1 人の確認レベルのトラフィックには十分

**メモリ 1GB：**
- Python インタプリタ: ~50-100 MB
- PostgreSQL (最小): ~50-100 MB
- FastAPI + Uvicorn: ~100-200 MB
- 余裕: ~600-700 MB
- **軽微なトラフィックなら十分**

**ストレージ 20GB：**
- Ubuntu 22.04 LTS: ~2.5 GB
- PostgreSQL: ~1-3 GB（初期時点）
- アプリケーション・ライブラリ: ~1-2 GB
- 余裕: ~15 GB

---

## EC2インスタンスの初期セットアップ

### 前提条件
- EC2インスタンス（Ubuntu 22.04 LTS推奨）
- Elastic IPアドレスを割り当て（固定IP）
- セキュリティグループでポート22（SSH）、5432（PostgreSQL）、8000（FastAPI）を開放

### SSHキーペアの取得

#### AWS Management Console から取得（初回のみ）

1. **EC2ダッシュボードを開く**
   - AWS Management Consoleにログイン
   - EC2 → インスタンスを起動

2. **インスタンス作成時にキーペアを生成**
   - 「ステップ 3: インスタンスの詳細設定」で進む
   - 「ステップ 6: セキュリティグループの設定」で進む
   - 「ステップ 7: 確認」画面に到達
   - 「起動」クリック → キーペア作成ダイアログが表示

3. **新しいキーペアを作成**
   - キーペア名: `fastapi-backlog-key`（任意）
   - キーペアタイプ: `RSA`
   - ファイル形式: `PEM`（Macの場合）or `PPK`（PuTTYの場合）
   - 「キーペアをダウンロード」
   - **`fastapi-backlog-key.pem` がダウンロードされる**

4. **キーのパーミッション設定**（Linux/Mac）
```bash
chmod 400 ~/Downloads/fastapi-backlog-key.pem
```

#### 既に存在するキーペアを確認

既にキーペアを作成済みの場合：
```bash
# AWS CLIで確認
aws ec2 describe-key-pairs --query 'KeyPairs[*].[KeyName]' --output text

# または AWS Management Consoleで確認
# EC2 → キーペア → キーペア一覧を表示
```

#### キーを紛失した場合

残念ながら、紛失したキーペアのダウンロードはできません。以下の対策が必要：

**オプション 1: 新しいインスタンスを作成**
```bash
# 新しいキーペアを生成して新しいインスタンスを起動
```

**オプション 2: EC2 Instance Connect を使用（Ubuntu の場合）**
```bash
# AWS CLIでSSH接続（キー不要）
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-xxxxxxxxxx \
  --os-user ubuntu \
  --ssh-public-key file://~/.ssh/id_rsa.pub \
  --availability-zone ap-northeast-1a
```

---

### SSHで接続
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### システムパッケージの更新
```bash
sudo apt update
sudo apt upgrade -y
```

---

## Python、PostgreSQL、uvのインストール

### 0. Gitのインストール
```bash
sudo apt install -y git
git --version
```

### 1. Python 3.11+のインストール
```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

### 2. PostgreSQLのインストール
```bash
sudo apt install -y postgresql postgresql-contrib libpq-dev
```

### 3. Rustのインストール（uvが必要）
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### 4. uvのインストール
```bash
pip install --upgrade pip
pip install uv
```

### インストール確認
```bash
python3.11 --version
psql --version
uv --version
```

---

## FastAPIアプリケーションのセットアップ

### 1. プロジェクトディレクトリの作成と移動
```bash
cd ~
mkdir -p projects/fastapi-backlog
cd projects/fastapi-backlog
```

### 2. プロジェクトファイルをアップロード
ローカルからEC2にファイルをコピー：
```bash
# ローカルマシンから実行
scp -i your-key.pem -r /path/to/0521_fastapi_backlog/* ubuntu@your-ec2-ip:~/projects/fastapi-backlog/
```

### 3. 仮想環境の作成と依存パッケージのインストール
```bash
cd ~/projects/fastapi-backlog
python3.11 -m venv venv
source venv/bin/activate
uv pip install -r requirements.txt
```

### 4. PostgreSQL接続情報の設定

EC2内でPostgresを起動・設定：
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

backlogデータベースとユーザーを作成：
```bash
sudo -u postgres psql << EOF
CREATE USER backlog_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE backlog OWNER backlog_user;
GRANT ALL PRIVILEGES ON DATABASE backlog TO backlog_user;
\q
EOF
```

`.env` ファイルを作成：
```bash
cat > ~/projects/fastapi-backlog/.env << EOF
DATABASE_URL=postgresql://backlog_user:secure_password_here@localhost:5432/backlog
EOF
```

### 5. マイグレーションの実行
```bash
cd ~/projects/fastapi-backlog
source venv/bin/activate
alembic upgrade head
```

### 6. FastAPIサーバの起動

#### 開発環境での起動（テスト用）
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 本番環境での起動（バックグラウンド）
**オプション A: systemdサービスで管理**

`/etc/systemd/system/fastapi-backlog.service` を作成：
```bash
sudo tee /etc/systemd/system/fastapi-backlog.service > /dev/null << EOF
[Unit]
Description=FastAPI Backlog Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/projects/fastapi-backlog
Environment="PATH=/home/ubuntu/projects/fastapi-backlog/venv/bin"
ExecStart=/home/ubuntu/projects/fastapi-backlog/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

サービスを有効化・起動：
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi-backlog
sudo systemctl start fastapi-backlog
```

ステータス確認：
```bash
sudo systemctl status fastapi-backlog
```

**オプション B: screen/tmuxで起動**
```bash
screen -S fastapi -d -m bash -c "cd ~/projects/fastapi-backlog && source venv/bin/activate && uv run uvicorn main:app --host 0.0.0.0 --port 8000"
```

### 7. セキュリティグループの設定確認
AWS Management Consoleでセキュリティグループを確認：
- **インバウンドルール**
  - ポート 8000 (TCP): どこからでもアクセス可能 (0.0.0.0/0)
  - ポート 5432 (TCP): ローカルマシンのIPアドレスのみ

---

## ローカルからPostgresへのアクセス

### 1. EC2のPostgresをリモートアクセス対応にする

EC2内で`/etc/postgresql/14/main/postgresql.conf`を編集：
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

以下の行を探して編集：
```
listen_addresses = '*'
```

`/etc/postgresql/14/main/pg_hba.conf`を編集：
```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

最後に以下を追加：
```
host    all             all             0.0.0.0/0               md5
```

PostgreSQLを再起動：
```bash
sudo systemctl restart postgresql
```

### 2. ローカルマシンから接続

#### a) psqlで直接接続
```bash
psql -h your-ec2-ip -U backlog_user -d backlog -p 5432
```

パスワードを聞かれたら、`secure_password_here` を入力

#### b) PythonのSQLAlchemyで接続
```python
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://backlog_user:secure_password_here@your-ec2-ip:5432/backlog"
engine = create_engine(DATABASE_URL)

# テスト接続
with engine.connect() as conn:
    print("Connected successfully!")
```

#### c) DBeaver、TablePlus、pgAdminなどGUIツールで接続
- **Host**: your-ec2-ip（Elastic IP）
- **Port**: 5432
- **Database**: backlog
- **User**: backlog_user
- **Password**: secure_password_here

### 3. SSH トンネル経由で接続（より安全）

ローカルマシンからSSHトンネルを構築：
```bash
ssh -i your-key.pem -L 5432:localhost:5432 ubuntu@your-ec2-ip
```

別のターミナルでローカルホストに接続：
```bash
psql -h localhost -U backlog_user -d backlog -p 5432
```

### 4. セキュリティベストプラクティス

セキュリティグループでPostgresへのアクセスを制限：
```bash
# ローカルマシンのIPのみ許可
# AWS Management Consoleで:
# Inbound Rule: PostgreSQL (5432) → Your IP/32
```

---

## トラブルシューティング

### FastAPIが起動しない
```bash
# ログ確認
sudo journalctl -u fastapi-backlog -f

# または手動起動でエラーを確認
cd ~/projects/fastapi-backlog
source venv/bin/activate
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Postgresに接続できない
```bash
# PostgreSQLが起動しているか確認
sudo systemctl status postgresql

# ファイアウォール確認
sudo ufw allow 5432/tcp

# 接続テスト
sudo -u postgres psql -c "SELECT 1"
```

### ポート8000が既に使用されている
```bash
# 別のプロセスを確認
sudo lsof -i :8000

# 別のポートで起動
uv run uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## APIへのアクセス

EC2が起動したら、ローカルマシンから以下でアクセス可能：

- **API**: http://your-ec2-ip:8000
- **Swagger UI**: http://your-ec2-ip:8000/docs
- **ReDoc**: http://your-ec2-ip:8000/redoc

---

## 参考リンク

- [FastAPI デプロイメント](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL リモートアクセス](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [uv ドキュメント](https://docs.astral.sh/uv/)
