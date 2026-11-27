"""
docs/quickstart.md says, by its detk-de deseq2 example, how detk's DESeq2
differs from a default results() call: it names independent filtering and
Cook's distance and links docs/tools/de.md, whose deseq2 section states the
results() settings detk matches, and the R it shows passes both to
results() (DETK-0770).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUICKSTART = ROOT / "docs" / "quickstart.md"
DE = ROOT / "docs" / "tools" / "de.md"

TERMS = ("independent filtering", "Cook's distance")


def _by_the_example():
    "The prose after the quickstart's first code block that runs detk-de deseq2, up to the next heading"
    text = QUICKSTART.read_text()
    m = re.search(
        r"```bash\n(?:(?!```).)*?detk-de deseq2(?:(?!```).)*?```\n(.*?)(?=^#)", text, re.S | re.M
    )
    assert m, "docs/quickstart.md has no bash example running detk-de deseq2"
    return m.group(1)


def _de_deseq2_section():
    text = DE.read_text()
    start = text.index("## `deseq2`")
    end = text.index("\n## ", start + 1)
    return text[start:end]


def test_quickstart_names_how_deseq2_differs():
    prose = _by_the_example()
    for term in TERMS:
        assert term.lower() in prose.lower(), (
            f"docs/quickstart.md does not name {term!r} by its detk-de deseq2 example"
        )


def test_quickstart_links_de_page_by_the_example():
    prose = _by_the_example()
    assert re.search(r"\]\(tools/de\.md(#deseq2)?\)", prose), (
        "docs/quickstart.md does not link docs/tools/de.md by its detk-de deseq2 example"
    )


def test_de_page_states_the_matched_settings():
    section = _de_deseq2_section()
    assert "no independent filtering" in section
    assert "Cook's distance" in section
    assert "results(" in section


def test_de_page_r_block_turns_off_both():
    "The R the page calls roughly equivalent passes both settings to results() (DETK-0770)"
    section = _de_deseq2_section()
    calls = re.findall(r"results\(dds[^)]*\)", section)
    assert calls, "docs/tools/de.md's deseq2 section has no results(dds, ...) call"
    for call in calls:
        assert re.search(r"independentFiltering\s*=\s*FALSE", call), (
            f"{call} in docs/tools/de.md applies independent filtering"
        )
        assert re.search(r"cooksCutoff\s*=\s*Inf", call), (
            f"{call} in docs/tools/de.md applies a Cook's distance cutoff"
        )
