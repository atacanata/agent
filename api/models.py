from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: str


class Project(BaseModel):
    id: str
    name: str
    description: str | None = None


class Run(BaseModel):
    id: str
    project_id: str
    status: Literal["queued", "running", "blocked", "failed", "succeeded"]
    checkpoint: Literal["A", "B", "C"]
    started_at: datetime | None = None
    updated_at: datetime | None = None


class Artifact(BaseModel):
    name: str
    content_type: str | None = None
    size_bytes: int | None = None
    updated_at: datetime | None = None
