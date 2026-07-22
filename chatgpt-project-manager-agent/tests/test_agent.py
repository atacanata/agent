from pathlib import Path

from chatgpt_pm_agent import (
    CommandResult,
    CycleState,
    Decision,
    Evidence,
    classify_decision,
    load_state,
    render_report,
    save_state,
)


def test_decision_requires_explicit_line():
    assert classify_decision("REVISE\nDüzelt.") is Decision.REVISE
    assert classify_decision("KARAR: DONE\nTamamlandı.") is Decision.DONE
    assert classify_decision("Bence devam edilebilir.") is Decision.UNCLEAR


def test_state_round_trip(tmp_path: Path):
    state = CycleState(
        1,
        "Deneme",
        "D:\\Deneme",
        "Hakem",
        "Test ekle",
    )
    save_state(tmp_path, state)
    assert load_state(tmp_path).cycle_id == 1


def test_report_shows_failure():
    state = CycleState(
        1,
        "Deneme",
        "D:\\Deneme",
        "Hakem",
        "Düzelt",
    )
    evidence = Evidence(
        project_path="D:\\Deneme",
        branch="main",
        head="abc",
        git_status=" M app.py",
        git_diff="-eski\n+yeni",
        changed_files=["app.py"],
        tests=[CommandResult("pytest -q", 1, "1 failed", "")],
    )
    report = render_report(state, evidence)
    assert "Test 1: FAIL" in report
    assert "app.py" in report
    assert "1 failed" in report
