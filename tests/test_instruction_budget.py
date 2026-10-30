"""AGENTS.md holds always-true facts; procedures live in the owning skills."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "")).lower()


def test_agents_md_under_budget():
    text = AGENTS.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 150
    assert len(text.split()) <= 1200


def test_no_rule_duplicated_more_than_once():
    text = _normalized(AGENTS.read_text(encoding="utf-8"))
    for phrase in ("update case_insights", "pain-first"):
        assert text.count(phrase) <= 1, f"{phrase!r} appears {text.count(phrase)} times"
