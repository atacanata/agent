from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chatgpt_pm_agent import (  # noqa: E402
    CommandResult,
    CycleState,
    Decision,
    Evidence,
    classify_decision,
    load_state,
    render_report,
    save_state,
)


class AgentTests(unittest.TestCase):
    def test_decision_requires_explicit_line(self) -> None:
        self.assertIs(classify_decision("REVISE\nDüzelt."), Decision.REVISE)
        self.assertIs(
            classify_decision("KARAR: DONE\nTamamlandı."),
            Decision.DONE,
        )
        self.assertIs(
            classify_decision("Bence devam edilebilir."),
            Decision.UNCLEAR,
        )

    def test_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            state = CycleState(
                1,
                "Deneme",
                "D:\\Deneme",
                "Hakem",
                "Test ekle",
            )
            save_state(directory, state)
            self.assertEqual(load_state(directory).cycle_id, 1)

    def test_report_shows_failure(self) -> None:
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
            tests=[CommandResult("unittest", 1, "1 failed", "")],
        )
        report = render_report(state, evidence)
        self.assertIn("Test 1: FAIL", report)
        self.assertIn("app.py", report)
        self.assertIn("1 failed", report)


if __name__ == "__main__":
    unittest.main()
