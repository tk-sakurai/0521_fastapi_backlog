from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import os

# PostgreSQLデータベース設定
# 環境変数 DATABASE_URL がなければデフォルト値を使用
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/backlog"
)

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """
    データベースセッション依存関係
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
