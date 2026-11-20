"""Tests of the tutorial runner on the fixture pages in pages/."""

from pathlib import Path

import pytest
from tutorial_runner import (
    TutorialError,
    TutorialFailure,
    TutorialSkip,
    discover,
    matches,
    parse,
    run_page,
)

PAGES = Path(__file__).parent / "pages"


def run(name, tmp_path, **kw):
    return run_page(PAGES / name, tmp_path / "work", **kw)


def test_passing_page_runs_every_bash_block_in_order(tmp_path):
    results = run("passes.md", tmp_path)
    page = parse(PAGES / "passes.md")
    bash = [b for b in page.blocks if b.lang == "bash"]
    assert [r.block.line for r in results] == [b.line for b in bash]
    # the hidden block ran, and in the page's working directory
    assert (tmp_path / "work" / "work" / "hidden.txt").read_text() == "hidden ran\n"
    assert (tmp_path / "work" / "work" / "help.txt").read_text().strip()


def test_markers_are_parsed(tmp_path):
    page = parse(PAGES / "passes.md")
    assert page.marked and page.requires == [["bash"]]
    langs = [b.lang for b in page.blocks]
    assert "console" in langs and "python" in langs
    assert [b.expect for b in page.blocks if b.expect is not None] == ["", "", "", "regex", ""]
    assert sum(b.fails for b in page.blocks) == 1
    hidden = [b for b in page.blocks if b.hidden]
    assert len(hidden) == 1 and "hidden ran" in hidden[0].code


def test_missing_requirements_skip_with_the_reason(tmp_path):
    with pytest.raises(TutorialSkip) as e:
        run("requires_missing.md", tmp_path, require_all=False)
    msg = str(e.value)
    assert "requires_missing.md" in msg
    assert "no-such-program-detk is not on PATH" in msg
    # R itself, or the package, is reported missing
    assert "R (Rscript) is not on PATH" in msg or "NoSuchPackageDetk" in msg


def test_require_all_turns_a_skip_into_a_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("DETK_TUTORIALS_REQUIRE_ALL", "1")
    with pytest.raises(TutorialFailure, match="no-such-program-detk"):
        run("requires_missing.md", tmp_path)


def test_failing_block_reports_page_line_and_stderr(tmp_path):
    with pytest.raises(TutorialFailure) as e:
        run("block_fails.md", tmp_path)
    msg = str(e.value)
    assert msg.startswith("tests/tutorials/pages/block_fails.md:7: block exited 1")
    assert "something went wrong" in msg.split("--- stderr ---")[1]
    assert "to stdout" in msg.split("--- stdout ---")[1]
    assert "never reached" not in msg.split("--- stdout ---")[1]


@pytest.mark.parametrize("name", ["pipe_fails.md", "unset_fails.md"])
def test_blocks_run_under_pipefail_and_nounset(tmp_path, name):
    with pytest.raises(TutorialFailure, match=f"{name}:3: block exited"):
        run(name, tmp_path)


def test_expect_mismatch_reports_both_outputs(tmp_path):
    with pytest.raises(TutorialFailure) as e:
        run("expect_mismatch.md", tmp_path)
    msg = str(e.value)
    assert "expect_mismatch.md:8: the stdout of the block at line 3 does not match" in msg
    assert "the output shown" in msg and "actual output" in msg


def test_fails_block_that_succeeds_is_a_failure(tmp_path):
    with pytest.raises(TutorialFailure, match="expected to fail"):
        run("fails_but_passes.md", tmp_path)


def test_each_run_starts_in_a_fresh_directory(tmp_path):
    run_page(PAGES / "passes.md", tmp_path / "one")
    run_page(PAGES / "passes.md", tmp_path / "two")
    assert (tmp_path / "two" / "work" / "counts.csv").exists()


@pytest.mark.parametrize(
    "expected, actual, regex, ok",
    [
        ("a\nb", "a  \nb\n\n", False, True),
        ("a\nb", "a\nc", False, False),
        ("x = 1.2...", "x = 1.2345", False, True),
        ("start\n...\nend", "start\n1\n2\nend", False, True),
        ("a.b", "axb", False, False),  # '.' is literal without regex
        (r"n = \d+", "n = 42", True, True),
        (r"n = \d+", "n = 42 extra", True, False),
    ],
)
def test_matches(expected, actual, regex, ok):
    assert matches(expected, actual, regex=regex) is ok


@pytest.mark.parametrize(
    "text, error",
    [
        ("<!-- tutorial: expect -->\n\nsome prose\n\n```text\nx\n```\n", "right before"),
        ("<!-- tutorial: fails -->\n```text\nx\n```\n", "bash block"),
        ("<!-- tutorial: hidden -->\n", "between"),
        ("<!-- tutorial: hidden\n```bash\ntrue\n```\n", "never closed"),
        ("<!-- tutorial: requires -->\n", "names nothing"),
        ("<!-- tutorial: frobnicate -->\n", "unknown tutorial marker"),
        ("```bash\ntrue\n", "unclosed"),
        ("<!-- tutorial: expect -->\n", "before no block"),
    ],
)
def test_bad_markers_are_errors(tmp_path, text, error):
    p = tmp_path / "bad.md"
    p.write_text(text)
    with pytest.raises(TutorialError, match=error):
        parse(p)


def test_expect_without_a_preceding_block_is_an_error(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text("<!-- tutorial: expect -->\n```text\nx\n```\n")
    with pytest.raises(TutorialError, match="follows no bash block"):
        run_page(p, tmp_path / "work")


def test_markers_inside_code_fences_are_ignored(tmp_path):
    p = tmp_path / "howto.md"
    p.write_text("````markdown\n<!-- tutorial: requires R -->\n```bash\nfalse\n```\n````\n")
    page = parse(p)
    assert not page.marked and page.requires == []
    assert [b.lang for b in page.blocks] == ["markdown"]


def test_discover_finds_tutorial_pages_and_marked_pages(tmp_path):
    docs = tmp_path / "docs"
    (docs / "tutorials").mkdir(parents=True)
    (docs / "recipes").mkdir()
    (docs / "tutorials" / "index.md").write_text("# Tutorials\n")
    (docs / "tutorials" / "one.md").write_text("# One\n")
    (docs / "recipes" / "marked.md").write_text("# R\n\n<!-- tutorial -->\n")
    (docs / "recipes" / "plain.md").write_text("# P\n\n```bash\ntrue\n```\n")
    found = [p.relative_to(docs).as_posix() for p in discover(docs)]
    assert found == ["recipes/marked.md", "tutorials/one.md"]


# the fixture a tests/tutorials/test_<page>.py uses for deeper checks


def test_tutorial_workdir_gives_the_directory_after_the_page_ran(tutorial_workdir):
    workdir = tutorial_workdir(PAGES / "passes.md")
    assert (workdir / "work" / "counts.csv").read_text().startswith("gene,a,b")
    # the page runs once per session; a second call returns the same run
    assert tutorial_workdir(PAGES / "passes.md") == workdir


def test_tutorial_workdir_skips_when_the_page_skips(tutorial_runs):
    workdir, error = tutorial_runs(PAGES / "requires_missing.md")
    assert isinstance(error, (TutorialSkip, TutorialFailure))


def test_tutorial_workdir_fails_when_the_page_fails(tutorial_runs):
    _, error = tutorial_runs(PAGES / "block_fails.md")
    assert isinstance(error, TutorialFailure) and "block_fails.md:7" in str(error)


def test_markers_and_hidden_blocks_do_not_show_on_the_site():
    # renders with the site's Markdown extensions; needs the docs group
    # (uv run --group docs pytest tests/tutorials)
    markdown = pytest.importorskip("markdown")
    import re

    yaml = pytest.importorskip("yaml")

    config = yaml.safe_load((Path(__file__).parents[2] / "mkdocs.yml").read_text())
    extensions = [e if isinstance(e, str) else next(iter(e)) for e in config["markdown_extensions"]]
    html = markdown.markdown((PAGES / "passes.md").read_text(), extensions=extensions)
    visible = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    assert "tutorial" not in visible
    assert "hidden ran" not in visible
    assert "hidden ran" in html  # rendered, but inside the comment
