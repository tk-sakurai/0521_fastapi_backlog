from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    projectKey = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    chartEnabled = Column(Boolean, default=False)
    useResolvedForChart = Column(Boolean, default=False)
    subtaskingEnabled = Column(Boolean, default=False)
    projectLeaderCanEditProjectLeader = Column(Boolean, default=False)
    useWiki = Column(Boolean, default=True)
    useFileSharing = Column(Boolean, default=True)
    useWikiTreeView = Column(Boolean, default=True)
    useOriginalImageSizeAtWiki = Column(Boolean, default=False)
    useSubversion = Column(Boolean, default=True)
    useGit = Column(Boolean, default=True)
    textFormattingRule = Column(String(50), default="markdown")
    archived = Column(Boolean, default=False)
    displayOrder = Column(Integer, default=2147483646)
    useDevAttributes = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    issues = relationship(
        "Issue", back_populates="project", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "projectKey": self.projectKey,
            "name": self.name,
            "chartEnabled": self.chartEnabled,
            "useResolvedForChart": self.useResolvedForChart,
            "subtaskingEnabled": self.subtaskingEnabled,
            "projectLeaderCanEditProjectLeader": self.projectLeaderCanEditProjectLeader,
            "useWiki": self.useWiki,
            "useFileSharing": self.useFileSharing,
            "useWikiTreeView": self.useWikiTreeView,
            "useOriginalImageSizeAtWiki": self.useOriginalImageSizeAtWiki,
            "useSubversion": self.useSubversion,
            "useGit": self.useGit,
            "textFormattingRule": self.textFormattingRule,
            "archived": self.archived,
            "displayOrder": self.displayOrder,
            "useDevAttributes": self.useDevAttributes,
        }


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    projectId = Column(Integer, ForeignKey("projects.id"), nullable=False)
    issueKey = Column(String(255), unique=True, index=True, nullable=False)
    keyId = Column(Integer, nullable=False)
    issueTypeId = Column(Integer, nullable=False)
    summary = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resolution = Column(String(255), nullable=True)
    priorityId = Column(Integer, nullable=False)
    statusId = Column(Integer, default=1)
    startDate = Column(String(10), nullable=True)  # yyyy-MM-dd format
    dueDate = Column(String(10), nullable=True)  # yyyy-MM-dd format
    assigneeId = Column(Integer, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    project = relationship("Project", back_populates="issues")

    def to_dict(self):
        return {
            "id": self.id,
            "projectId": self.projectId,
            "issueKey": self.issueKey,
            "keyId": self.keyId,
            "issueType": {
                "id": self.issueTypeId,
                "projectId": self.projectId,
                "name": "タスク (Mock)",
                "color": "#7ea800",
                "displayOrder": 0,
            },
            "summary": self.summary,
            "description": self.description or "",
            "resolution": self.resolution,
            "priority": {
                "id": self.priorityId,
                "name": "中 (Mock)",
            },
            "status": {
                "id": self.statusId,
                "projectId": self.projectId,
                "name": "未対応",
                "color": "#ed8077",
                "displayOrder": 1000,
            },
            "startDate": self.startDate,
            "dueDate": self.dueDate,
            "assigneeId": self.assigneeId,
            "created": self.created.isoformat() + "Z" if self.created else None,
        }
