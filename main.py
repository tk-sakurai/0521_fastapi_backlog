from fastapi import FastAPI, Depends, Form, HTTPException, Header, Query, status
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Project, Issue
from datetime import datetime

# テーブルの初期化
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Backlog API Mock")


class Body(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


# Response Models
class ProjectResponse(BaseModel):
    id: int
    projectKey: str
    name: str
    chartEnabled: bool
    useResolvedForChart: bool
    subtaskingEnabled: bool
    projectLeaderCanEditProjectLeader: bool
    useWiki: bool
    useFileSharing: bool
    useWikiTreeView: bool
    useOriginalImageSizeAtWiki: bool
    useSubversion: bool
    useGit: bool
    textFormattingRule: str
    archived: bool
    displayOrder: int
    useDevAttributes: bool


class IssueTypeResponse(BaseModel):
    id: int
    projectId: int
    name: str
    color: str
    displayOrder: int


class PriorityResponse(BaseModel):
    id: int
    name: str


class StatusResponse(BaseModel):
    id: int
    projectId: int
    name: str


class IssueResponse(BaseModel):
    id: int
    projectId: int
    issueKey: str
    keyId: int
    issueType: IssueTypeResponse
    summary: str
    description: str
    resolution: Optional[str] = None
    priority: PriorityResponse
    status: StatusResponse
    startDate: Optional[str] = None
    dueDate: Optional[str] = None
    assigneeId: Optional[int] = None


def verify_backlog_auth(
    apiKey: Optional[str] = Query(None, description="APIキーによる認証"),
):
    """
    Backlog APIの認証をチェックする依存関係関数
    ドキュメント通り、apiKeyのクエリパラメータを確認します。
    """
    # 1. APIキー認証のチェック
    if apiKey is not None:
        if apiKey != "valid_api_key_12345":
            raise HTTPException(status_code=401, detail="Invalid API Key")
        return {"auth_method": "api_key"}
    raise HTTPException(status_code=401, detail="Authentication required")


@app.post(
    "/api/v2/projects",
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトの追加",
    response_model=ProjectResponse,
)
def add_project(
    name: str = Form(...),
    key: str = Form(...),
    subtaskingEnabled: bool = Form(False),
    textFormattingRule: str = Form("markdown"),
    # include a few other fields
    auth_info: dict = Depends(verify_backlog_auth),
    db: Session = Depends(get_db),
):
    # 既存のプロジェクトキーをチェック
    existing_project = db.query(Project).filter(Project.projectKey == key).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project key already exists")

    # 新しいプロジェクトを作成
    new_project = Project(
        projectKey=key,
        name=name,
        subtaskingEnabled=subtaskingEnabled,
        textFormattingRule=textFormattingRule,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project.to_dict()


@app.post(
    "/api/v2/issues",
    status_code=status.HTTP_201_CREATED,
    summary="課題の追加",
    response_model=IssueResponse,
)
def add_issue(
    projectId: int = Form(..., description="課題を登録するプロジェクトのID"),
    summary: str = Form(..., description="課題の件名"),
    issueTypeId: int = Form(..., description="課題の種別のID"),
    priorityId: int = Form(..., description="課題の優先度のID"),
    description: Optional[str] = Form(None, description="課題の詳細"),
    startDate: Optional[str] = Form(None, description="課題の開始日 (yyyy-MM-dd)"),
    dueDate: Optional[str] = Form(None, description="課題の期限日 (yyyy-MM-dd)"),
    assigneeId: Optional[int] = Form(None, description="課題の担当者のユーザーのID"),
    auth_info: dict = Depends(verify_backlog_auth),
    db: Session = Depends(get_db),
):
    # プロジェクトの存在確認
    project = db.query(Project).filter(Project.id == projectId).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 次のkeyIdを計算（プロジェクト内での連番）
    last_issue = (
        db.query(Issue)
        .filter(Issue.projectId == projectId)
        .order_by(Issue.keyId.desc())
        .first()
    )
    next_key_id = (last_issue.keyId + 1) if last_issue else 1
    issue_key = f"{project.projectKey}-{next_key_id}"

    # 新しい課題を作成
    new_issue = Issue(
        projectId=projectId,
        issueKey=issue_key,
        keyId=next_key_id,
        issueTypeId=issueTypeId,
        summary=summary,
        description=description or "",
        priorityId=priorityId,
        startDate=startDate,
        dueDate=dueDate,
        assigneeId=assigneeId,
    )

    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)

    return new_issue.to_dict()
