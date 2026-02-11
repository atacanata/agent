from __future__ import annotations

import mimetypes
import re
from datetime import datetime, timezone
import os
from pathlib import Path

import yaml

from .models import Artifact, Project, Run

BACKLOG_DIR: Path | None = None
RUNBOOK_DIR: Path | None = None

_REPO_ROOT_ENV_KEYS = (
    "AI_TEAM_REPO_ROOT",
    "AGENT_REPO_ROOT",
    "REPO_ROOT",
)

_CI_PATTERN = re.compile(r"^ci_(?P<run_id>.+)\.log$")


def _as_utc(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _iter_repo_root_env_keys() -> list[str]:
    keys = list(_REPO_ROOT_ENV_KEYS)
    wildcard = sorted(
        key for key in os.environ if key.endswith("REPO_ROOT") and key not in keys
    )
    keys.extend(wildcard)
    return keys


def _resolve_repo_root() -> Path:
    for key in _iter_repo_root_env_keys():
        value = os.getenv(key)
        if value:
            return Path(value).expanduser()
    return _default_repo_root()


def _coerce_dir(override: Path | str | None) -> Path | None:
    if override is None:
        return None
    if isinstance(override, Path):
        return override
    return Path(override)


def _backlog_dir() -> Path:
    override = _coerce_dir(BACKLOG_DIR)
    if override is not None:
        return override
    return _resolve_repo_root() / "tasks" / "backlog"


def _runbook_dir() -> Path:
    override = _coerce_dir(RUNBOOK_DIR)
    if override is not None:
        return override
    return _resolve_repo_root() / "docs" / "RUNBOOK"


def list_projects() -> list[Project]:
    projects: list[Project] = []
    backlog_dir = _backlog_dir()
    for path in sorted(backlog_dir.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as fh:
            payload = yaml.safe_load(fh) or {}

        project_id = payload.get("project_id")
        if not project_id:
            continue

        projects.append(
            Project(
                id=str(project_id),
                name=str(payload.get("title") or project_id),
                description=payload.get("goal"),
            )
        )
    return projects


def project_exists(project_id: str) -> bool:
    return any(project.id == project_id for project in list_projects())


def list_run_ids() -> list[str]:
    run_ids: list[str] = []
    runbook_dir = _runbook_dir()
    for path in sorted(runbook_dir.glob("ci_*.log")):
        match = _CI_PATTERN.match(path.name)
        if match:
            run_ids.append(match.group("run_id"))
    return run_ids


def _read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _status_for_run(run_id: str) -> str:
    runbook_dir = _runbook_dir()
    test_text = _read_text_if_exists(runbook_dir / f"test_{run_id}.md")
    review_text = _read_text_if_exists(runbook_dir / f"review_{run_id}.md")

    if "RESULT: PASS" in test_text and "VERDICT: APPROVE" in review_text:
        return "succeeded"
    if "RESULT: FAIL" in test_text:
        return "failed"

    required = [
        runbook_dir / f"test_{run_id}.md",
        runbook_dir / f"diff_{run_id}.patch",
        runbook_dir / f"review_{run_id}.md",
    ]
    if all(path.is_file() for path in required):
        return "running"
    return "blocked"


def list_run_artifact_paths(run_id: str) -> list[Path]:
    runbook_dir = _runbook_dir()
    return sorted(path for path in runbook_dir.glob(f"*_{run_id}.*") if path.is_file())


def list_runs(project_id: str) -> list[Run]:
    runs: list[Run] = []
    for run_id in list_run_ids():
        runbook_dir = _runbook_dir()
        ci_path = runbook_dir / f"ci_{run_id}.log"
        artifacts = list_run_artifact_paths(run_id)
        updated_ts = max((path.stat().st_mtime for path in artifacts), default=ci_path.stat().st_mtime)
        runs.append(
            Run(
                id=run_id,
                project_id=project_id,
                status=_status_for_run(run_id),
                checkpoint="C",
                started_at=_as_utc(ci_path.stat().st_mtime),
                updated_at=_as_utc(updated_ts),
            )
        )
    return runs


def get_run(project_id: str, run_id: str) -> Run | None:
    for run in list_runs(project_id):
        if run.id == run_id:
            return run
    return None


def list_artifacts(run_id: str) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for path in list_run_artifact_paths(run_id):
        content_type, _ = mimetypes.guess_type(path.name)
        stat = path.stat()
        artifacts.append(
            Artifact(
                name=path.name,
                content_type=content_type or "application/octet-stream",
                size_bytes=stat.st_size,
                updated_at=_as_utc(stat.st_mtime),
            )
        )
    return artifacts


def get_artifact_path(run_id: str, name: str) -> Path | None:
    # Reject names that can escape the runbook directory.
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        return None

    runbook_dir = _runbook_dir()
    candidate = (runbook_dir / name).resolve()
    runbook_resolved = runbook_dir.resolve()
    try:
        candidate.relative_to(runbook_resolved)
    except ValueError:
        return None

    if not candidate.is_file():
        return None

    expected = {artifact.name for artifact in list_artifacts(run_id)}
    if name not in expected:
        return None

    return candidate
