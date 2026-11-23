"""
The usage blocks of docs/tools/*.md and docs/report.md match the installed
--help, as tests/skills/test_skills.py checks the skill's (DETK-0010), so a
CLI change not carried into the docs fails CI. docs_usage.py says what a
usage block holds and regenerates them all.
"""

import pytest

import docs_usage as d

PAGES = sorted(d.PAGES)


@pytest.mark.parametrize("page", PAGES)
def test_usage_blocks_match_help(page):
    text = (d.DOCS / page).read_text()
    blocks = d.usage_blocks(text)
    assert blocks, f"docs/{page} has no usage block"
    for _, block in blocks:
        command = " ".join(d.command_of(block))
        assert block.rstrip("\n") == d.expected_block(block), (
            f"docs/{page}: the usage block of {command} is not its --help; "
            "run `uv run python tests/docs/docs_usage.py` to regenerate it"
        )


@pytest.mark.parametrize("page", PAGES)
def test_every_subcommand_has_a_usage_block(page):
    tool = d.PAGES[page]
    documented = {d.command_of(block) for _, block in d.usage_blocks((d.DOCS / page).read_text())}
    wanted = {(tool, sub) for sub in d.subcommands(tool)} or {(tool,)}
    missing = sorted(" ".join(c) for c in wanted - documented)
    assert not missing, f"docs/{page} has no usage block for {missing}"


def test_common_options_block_matches_help():
    text = (d.DOCS / d.COMMON_PAGE).read_text()
    blocks = [b for b in d.TEXT_BLOCK.findall(text) if b.startswith("common options:")]
    assert len(blocks) == 1, f"docs/{d.COMMON_PAGE} should show the common options once"
    assert blocks[0].rstrip("\n") == d.common_options(), (
        f"docs/{d.COMMON_PAGE}: the common options are not those of --help; "
        "run `uv run python tests/docs/docs_usage.py` to regenerate them"
    )


def test_every_subcommand_takes_the_common_options():
    # as docs/tools/index.md says: every subcommand, except that detk-util
    # record, which writes no table, has no -d
    common = d.common_options()
    without_delim = "\n".join(line for line in common.splitlines() if "--out-delim" not in line)
    for tool in d.PAGES.values():
        for sub in d.subcommands(tool) or [None]:
            argv = (tool, sub) if sub else (tool,)
            got = d.sections(d.help_text(*argv)).get("common options:")
            if argv == ("detk-util", "record"):
                # argparse realigns the column without -d's longer invocation
                assert got is not None and "--out-delim" not in got
                assert [line.split()[0] for line in got.splitlines()] == [
                    line.split()[0] for line in without_delim.splitlines()
                ]
            else:
                assert got == common, f"{' '.join(argv)} --help: common options differ"


def test_checker_catches_a_stale_block():
    stale = "usage: detk-norm deseq2 [options] <counts_fn>\n\noptions:\n  --bogus  Not an option\n"
    assert d.command_of(stale) == ("detk-norm", "deseq2")
    assert stale.rstrip("\n") != d.expected_block(stale)
    page = f"# x\n\n```text\n{stale}```\n"
    assert d.expected_block(stale) in d.regenerate(page)
    # the docopt layout of the 0.x pages is found, and regenerated
    old = "Usage:\n    detk-norm cpm [options] <counts_fn>\n"
    assert d.command_of(old) == ("detk-norm", "cpm")
    assert d.regenerate(f"```text\n{old}```\n").startswith("```text\nusage: detk-norm cpm")
