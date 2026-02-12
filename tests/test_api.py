from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from api import repository


@pytest.fixture()
def seeded_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    backlog_dir = tmp_path / "tasks" / "backlog"
    runbook_dir = tmp_path / "docs" / "RUNBOOK"
    backlog_dir.mkdir(parents=True)
    runbook_dir.mkdir(parents=True)

    (backlog_dir / "PRJ-001.yaml").write_text(
        "project_id: PRJ-001\n"
        "title: Agent AI Team Runner (VDS)\n"
        "goal: Sample goal\n",
        encoding="utf-8",
    )

    run_id = "20260211_999999"
    (runbook_dir / f"ci_{run_id}.log").write_text("ci output\n", encoding="utf-8")
    (runbook_dir / f"test_{run_id}.md").write_text("RESULT: PASS\n", encoding="utf-8")
    (runbook_dir / f"review_{run_id}.md").write_text("VERDICT: APPROVE\n", encoding="utf-8")
    (runbook_dir / f"diff_{run_id}.patch").write_text("diff --git a/x b/x\n", encoding="utf-8")

    monkeypatch.setattr(repository, "BACKLOG_DIR", backlog_dir)
    monkeypatch.setattr(repository, "RUNBOOK_DIR", runbook_dir)

    return {"project_id": "PRJ-001", "run_id": run_id}


def _request(method: str, path: str):
    async def _do():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path)

    return asyncio.run(_do())


def test_health_endpoint() -> None:
    response = _request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_projects_endpoint(seeded_repo: dict[str, str]) -> None:
    response = _request("GET", "/projects")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == seeded_repo["project_id"]
    assert payload[0]["name"] == "Agent AI Team Runner (VDS)"


def test_runs_and_run_detail_endpoints(seeded_repo: dict[str, str]) -> None:
    project_id = seeded_repo["project_id"]
    run_id = seeded_repo["run_id"]

    runs_response = _request("GET", f"/projects/{project_id}/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert len(runs) == 1
    assert runs[0]["id"] == run_id
    assert runs[0]["status"] == "succeeded"
    assert runs[0]["checkpoint"] == "C"

    run_response = _request("GET", f"/projects/{project_id}/runs/{run_id}")
    assert run_response.status_code == 200
    assert run_response.json()["id"] == run_id


def test_artifacts_list_and_download_endpoints(seeded_repo: dict[str, str]) -> None:
    project_id = seeded_repo["project_id"]
    run_id = seeded_repo["run_id"]

    list_response = _request("GET", f"/projects/{project_id}/runs/{run_id}/artifacts")
    assert list_response.status_code == 200
    names = {item["name"] for item in list_response.json()}
    assert {
        f"ci_{run_id}.log",
        f"test_{run_id}.md",
        f"review_{run_id}.md",
        f"diff_{run_id}.patch",
    } <= names

    download_response = _request(
        "GET", f"/projects/{project_id}/runs/{run_id}/artifacts/test_{run_id}.md"
    )
    assert download_response.status_code == 200
    assert "RESULT: PASS" in download_response.text


def test_not_found_and_path_traversal(seeded_repo: dict[str, str]) -> None:
    project_id = seeded_repo["project_id"]
    run_id = seeded_repo["run_id"]

    missing_project = _request("GET", "/projects/UNKNOWN/runs")
    assert missing_project.status_code == 404

    traversal = _request(
        "GET", f"/projects/{project_id}/runs/{run_id}/artifacts/..%2F..%2Fetc%2Fpasswd"
    )
    assert traversal.status_code == 404
