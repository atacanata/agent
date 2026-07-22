from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Iterable


class Decision(StrEnum):
    CONTINUE = "CONTINUE"
    REVISE = "REVISE"
    INSPECT = "INSPECT"
    HOLD = "HOLD"
    ASK_USER = "ASK_USER"
    APPROVED = "APPROVED"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    UNCLEAR = "UNCLEAR"


@dataclass(slots=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


@dataclass(slots=True)
class Evidence:
    project_path: str
    branch: str | None = None
    head: str | None = None
    git_status: str = ""
    git_diff: str = ""
    changed_files: list[str] = field(default_factory=list)
    tests: list[CommandResult] = field(default_factory=list)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(slots=True)
class CycleState:
    cycle_id: int
    project_name: str
    project_path: str
    chat_title: str
    instruction: str
    status: str = "IN_PROGRESS"
    decision: Decision = Decision.UNCLEAR
    response: str = ""
    evidence_file: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class StateError(RuntimeError):
    pass


def load_config(path: Path) -> dict:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SystemExit(f"Yapılandırma okunamadı: {path}: {exc}") from exc


def config_paths(config_path: Path, config: dict) -> tuple[Path, Path]:
    project = Path(config["project"]["path"]).expanduser()
    state_dir = Path(config.get("state", {}).get("directory", ".\\state"))
    if not state_dir.is_absolute():
        state_dir = config_path.parent / state_dir
    return project.resolve(), state_dir.resolve()


def save_state(directory: Path, state: CycleState) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    state.updated_at = datetime.now(timezone.utc).isoformat()
    data = asdict(state)
    data["decision"] = state.decision.value
    target = directory / "cycle.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def load_state(directory: Path) -> CycleState:
    path = directory / "cycle.json"
    if not path.exists():
        raise StateError(f"Durum dosyası bulunamadı: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["decision"] = Decision(data.get("decision", "UNCLEAR"))
    return CycleState(**data)


def run(command: str, cwd: Path, timeout: int = 900) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return CommandResult(
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def git_text(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def collect(project_path: Path, test_commands: Iterable[str]) -> Evidence:
    if not project_path.is_dir():
        raise SystemExit(f"Proje yolu bulunamadı: {project_path}")

    status = git_text(["status", "--short"], project_path)
    return Evidence(
        project_path=str(project_path),
        branch=git_text(["branch", "--show-current"], project_path) or None,
        head=git_text(["rev-parse", "HEAD"], project_path) or None,
        git_status=status,
        git_diff=git_text(
            ["diff", "--no-ext-diff", "--binary"], project_path
        ),
        changed_files=[
            line[3:].strip()
            for line in status.splitlines()
            if len(line) >= 4
        ],
        tests=[run(command, project_path) for command in test_commands],
    )


def save_evidence(directory: Path, evidence: Evidence, cycle_id: int) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"evidence-cycle-{cycle_id:03d}.json"
    target.write_text(
        json.dumps(asdict(evidence), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def load_evidence(path: Path) -> Evidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["tests"] = [
        CommandResult(**item) for item in data.get("tests", [])
    ]
    return Evidence(**data)


DECISION_PATTERN = re.compile(
    r"(?im)^\s*(?:KARAR\s*[:\-]\s*)?"
    r"(CONTINUE|REVISE|INSPECT|HOLD|ASK_USER|APPROVED|DONE|BLOCKED)\b"
)


def classify_decision(response: str) -> Decision:
    match = DECISION_PATTERN.search(response)
    return Decision(match.group(1).upper()) if match else Decision.UNCLEAR


def trim(text: str, limit: int = 80_000) -> str:
    if len(text) <= limit:
        return text
    removed = len(text) - limit
    return text[:limit] + f"\n\n...[{removed} karakter kesildi]..."


def render_report(state: CycleState, evidence: Evidence) -> str:
    changed = (
        "\n".join(f"- `{item}`" for item in evidence.changed_files)
        or "- Yok"
    )

    test_blocks: list[str] = []
    for index, result in enumerate(evidence.tests, start=1):
        verdict = "PASS" if result.passed else "FAIL"
        test_blocks.append(
            f"### Test {index}: {verdict}\n"
            f"Komut: `{result.command}`\n"
            f"Çıkış kodu: {result.exit_code}\n\n"
            f"STDOUT:\n```text\n{trim(result.stdout, 20_000)}\n```\n\n"
            f"STDERR:\n```text\n{trim(result.stderr, 20_000)}\n```"
        )
    tests = "\n\n".join(test_blocks) or "Test komutu çalıştırılmadı."

    return f"""CHATGPT HAKEM RAPORU

## PROJE
- Proje: {state.project_name}
- Yol: `{state.project_path}`
- Dal: `{evidence.branch or 'Belirlenemedi'}`
- HEAD: `{evidence.head or 'Belirlenemedi'}`
- Tur: {state.cycle_id}

## ÖNCEKİ CHATGPT TALİMATI
{state.instruction.strip()}

## DEĞİŞEN DOSYALAR
{changed}

## GIT STATUS
```text
{evidence.git_status or 'Temiz veya Git deposu değil.'}
```

## GIT DIFF
```diff
{trim(evidence.git_diff) or 'Diff yok.'}
```

## TESTLER VE DOĞRULAMALAR
{tests}

## AÇIK SORUNLAR
- Ajanın kesin doğrulayamadığı noktalar açıkça belirtilmelidir.
- Görsel inceleme yapılmadıysa görsel olarak doğrulandığı iddia edilmemelidir.

## HAKEMDEN İSTENEN
Cevabın ilk anlamlı satırında şu kararlardan yalnız birini yaz:
CONTINUE, REVISE, INSPECT, HOLD, ASK_USER, APPROVED, DONE veya BLOCKED.

Ardından eksik kanıtları, kapsam dışı değişiklikleri ve uygulanacak sonraki talimatı açıkça yaz.
"""


def cmd_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    _, state_dir = config_paths(config_path, config)
    state_dir.mkdir(parents=True, exist_ok=True)
    print(f"Durum klasörü hazır: {state_dir}")
    return 0


def cmd_begin(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    project_path, state_dir = config_paths(config_path, config)
    instruction = Path(args.instruction_file).read_text(
        encoding="utf-8"
    ).strip()
    if not instruction:
        raise SystemExit("Talimat dosyası boş.")

    try:
        cycle_id = load_state(state_dir).cycle_id + 1
    except StateError:
        cycle_id = 1

    state = CycleState(
        cycle_id=cycle_id,
        project_name=config["project"]["name"],
        project_path=str(project_path),
        chat_title=config["chatgpt"]["conversation_title"],
        instruction=instruction,
    )
    print(
        f"Tur başlatıldı: {cycle_id}; "
        f"durum: {save_state(state_dir, state)}"
    )
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    project_path, state_dir = config_paths(config_path, config)
    state = load_state(state_dir)
    commands = args.test or list(
        config["project"].get("default_test_commands", [])
    )

    evidence = collect(project_path, commands)
    target = save_evidence(state_dir, evidence, state.cycle_id)
    state.evidence_file = str(target)
    save_state(state_dir, state)

    failed = sum(not result.passed for result in evidence.tests)
    print(
        f"Kanıt kaydedildi: {target}; "
        f"değişen dosya={len(evidence.changed_files)}; "
        f"başarısız test={failed}"
    )
    return 1 if failed else 0


def cmd_report(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    _, state_dir = config_paths(config_path, config)
    state = load_state(state_dir)
    if not state.evidence_file:
        raise SystemExit("Önce collect komutunu çalıştır.")

    report = render_report(
        state,
        load_evidence(Path(state.evidence_file)),
    )
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report + "\n", encoding="utf-8")
        print(f"Rapor yazıldı: {output}")
    else:
        print(report)
    return 0


def cmd_record_response(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    _, state_dir = config_paths(config_path, config)
    state = load_state(state_dir)
    response = Path(args.response_file).read_text(
        encoding="utf-8"
    ).strip()
    if not response:
        raise SystemExit("ChatGPT cevap dosyası boş.")

    decision = classify_decision(response)
    state.response = response
    state.decision = decision
    state.status = {
        Decision.DONE: "DONE",
        Decision.HOLD: "HOLD",
        Decision.ASK_USER: "WAITING_FOR_USER",
        Decision.BLOCKED: "BLOCKED",
    }.get(decision, "READY_FOR_NEXT_CYCLE")
    save_state(state_dir, state)

    print(
        json.dumps(
            {"decision": decision.value, "status": state.status},
            ensure_ascii=False,
        )
    )
    return 2 if decision is Decision.UNCLEAR else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chatgpt-pm")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("init")
    command.add_argument("--config", required=True)
    command.set_defaults(func=cmd_init)

    command = sub.add_parser("begin")
    command.add_argument("--config", required=True)
    command.add_argument("--instruction-file", required=True)
    command.set_defaults(func=cmd_begin)

    command = sub.add_parser("collect")
    command.add_argument("--config", required=True)
    command.add_argument("--test", action="append")
    command.set_defaults(func=cmd_collect)

    command = sub.add_parser("report")
    command.add_argument("--config", required=True)
    command.add_argument("--output")
    command.set_defaults(func=cmd_report)

    command = sub.add_parser("record-response")
    command.add_argument("--config", required=True)
    command.add_argument("--response-file", required=True)
    command.set_defaults(func=cmd_record_response)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except StateError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
