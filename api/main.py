from __future__ import annotations

import mimetypes

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .models import Artifact, Health, Project, Run
from .repository import (
    get_artifact_path,
    get_run,
    list_artifacts,
    list_projects,
    list_runs,
    project_exists,
)

app = FastAPI(
    title="Runner API",
    version="0.1.0",
    description="Minimal API for PRJ-001 runner (Stage B).",
    servers=[{"url": "/api"}],
)


@app.get("/health", response_model=Health)
async def health() -> Health:
    return Health(status="ok")


@app.get("/projects", response_model=list[Project])
async def projects() -> list[Project]:
    return list_projects()


@app.get("/projects/{project_id}/runs", response_model=list[Run])
async def project_runs(project_id: str) -> list[Run]:
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail="Resource not found")
    return list_runs(project_id)


@app.get("/projects/{project_id}/runs/{run_id}", response_model=Run)
async def project_run(project_id: str, run_id: str) -> Run:
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail="Resource not found")

    run = get_run(project_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return run


@app.get("/projects/{project_id}/runs/{run_id}/artifacts", response_model=list[Artifact])
async def run_artifacts(project_id: str, run_id: str) -> list[Artifact]:
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail="Resource not found")
    if get_run(project_id, run_id) is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return list_artifacts(run_id)


@app.get("/projects/{project_id}/runs/{run_id}/artifacts/{name}")
async def run_artifact(project_id: str, run_id: str, name: str) -> FileResponse:
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail="Resource not found")
    if get_run(project_id, run_id) is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    artifact_path = get_artifact_path(run_id, name)
    if artifact_path is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    media_type = mimetypes.guess_type(artifact_path.name)[0] or "application/octet-stream"
    return FileResponse(path=artifact_path, media_type=media_type, filename=artifact_path.name)
