"""
docs/agent-skills.md lists every file of the detk skill: SKILL.md and each
file under skills/detk/references/, by its path in the skill, in its "What
is in the skill" section (#121).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "detk"
PAGE = ROOT / "docs" / "agent-skills.md"


def _listed(text):
    "The files the page's 'What is in the skill' list names, as `path`: at an item's start"
    section = text[text.index("## What is in the skill") :]
    return set(re.findall(r"^- `([^`]+)`:", section, re.M))


def test_every_skill_file_is_listed():
    files = {"SKILL.md"} | {
        str(p.relative_to(SKILL)) for p in (SKILL / "references").rglob("*") if p.is_file()
    }
    listed = _listed(PAGE.read_text())
    missing = sorted(files - listed)
    assert not missing, f"docs/agent-skills.md does not list {missing} of skills/detk/"
    gone = sorted(listed - files)
    assert not gone, f"docs/agent-skills.md lists {gone}, which skills/detk/ does not have"


def test_the_check_sees_a_missing_file():
    text = PAGE.read_text().replace("- `references/covariates.md`:", "- covariates:")
    assert "references/covariates.md" not in _listed(text)
