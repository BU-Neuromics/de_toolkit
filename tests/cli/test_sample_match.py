"""
Counts and sample information whose sample sets differ are an error
(DETK-0600, #178).

detk 1.0.0 fitted the samples the two files shared and dropped the rest, with
nothing above INFO on stderr: the audit's case below (counts with samples
001-008, a sample sheet where 008 is 999) made ``detk-de deseq2`` fit seven
samples and exit 0. Now every command that matches a counts file to a sample
information file (through :class:`~de_toolkit.common.CountMatrix`) exits 1
naming the samples found in only one of them. The same samples in another
order are still matched by name; ``--strict`` still requires the same order.
``detk-util tidy`` is the explicit way to subset.
"""

import re

import numpy
import pandas
import pytest

import cli_adapter
from de_toolkit.common import CountMatrix, SampleMismatchException
from de_toolkit.wrapr import check_r, check_r_package

deseq2_test = pytest.mark.skipif(
    not (check_r() and check_r_package("DESeq2")), reason="R and DESeq2 are not installed"
)

SAMPLES = [f"{i:03d}" for i in range(1, 9)]


def _counts():
    rng = numpy.random.default_rng(600)
    n_features = 300
    base = rng.integers(50, 2000, size=n_features)
    data = {}
    for j, s in enumerate(SAMPLES):
        effect = 1.0 if j < 4 else numpy.where(numpy.arange(n_features) < 30, 3.0, 1.0)
        data[s] = rng.poisson(base * effect)
    frame = pandas.DataFrame(data, index=[f"{i:03d}" for i in range(n_features)])
    frame.index.name = "feature"
    return frame


def _sheet(samples=SAMPLES):
    "the sample information of *samples*: batch alternates, the first four are ctrl"
    samples = list(samples)
    return pandas.DataFrame(
        {
            "batch": ["a" if i % 2 == 0 else "b" for i in range(len(samples))],
            "condition": ["ctrl" if i < 4 else "treat" for i in range(len(samples))],
        },
        index=pandas.Index(samples, name="sample"),
    )


@pytest.fixture
def work(tmp_path, monkeypatch):
    "counts.csv (001-008); samples.csv (the same, in order); renamed.csv (008 is 999)"
    monkeypatch.chdir(tmp_path)
    _counts().to_csv(tmp_path / "counts.csv")
    _sheet().to_csv(tmp_path / "samples.csv")
    _sheet(SAMPLES[:-1] + ["999"]).to_csv(tmp_path / "renamed.csv")
    _sheet().iloc[::-1].to_csv(tmp_path / "reordered.csv")
    _sheet(SAMPLES + ["009"]).to_csv(tmp_path / "extra.csv")
    _sheet(SAMPLES[:-1]).to_csv(tmp_path / "missing.csv")
    return tmp_path


def assert_mismatch(outcome, prog, out, counts_only=("008",), sheet_only=("999",)):
    "exit 1, no output file, and one line on stderr naming the samples in only one file"
    assert outcome.code == 1, outcome.stderr
    assert not out.exists()
    line = outcome.stderr.strip().splitlines()[-1]
    assert line.startswith(f"{prog}: error: "), outcome.stderr
    # one line: the cause and nothing after it (no traceback without --verbose)
    assert "Traceback" not in outcome.stderr
    for s in counts_only:
        assert re.search(rf"counts only: [^;]*\b{s}\b", line), line
    for s in sheet_only:
        assert re.search(rf"sample information only: [^;]*\b{s}\b", line), line
    if not counts_only:
        assert "counts only" not in line, line
    if not sheet_only:
        assert "sample information only" not in line, line


# ------------------------------------------------------ the shared matching


def test_countmatrix_names_the_samples_in_only_one_file():
    with pytest.raises(SampleMismatchException) as e:
        CountMatrix(_counts(), _sheet(SAMPLES[:-1] + ["999"]))
    msg = str(e.value)
    assert "\n" not in msg
    assert re.search(r"counts only: 008\b", msg), msg
    assert re.search(r"sample information only: 999\b", msg), msg
    assert "detk-util tidy" in msg


@pytest.mark.parametrize(
    "samples,counts_only,sheet_only",
    [
        pytest.param(SAMPLES + ["009"], (), ("009",), id="extra-in-sheet"),
        pytest.param(SAMPLES[:-1], ("008",), (), id="missing-from-sheet"),
    ],
)
def test_countmatrix_any_difference_is_an_error(samples, counts_only, sheet_only):
    with pytest.raises(SampleMismatchException) as e:
        CountMatrix(_counts(), _sheet(samples))
    msg = str(e.value)
    for s in counts_only:
        assert re.search(rf"counts only: [^;]*\b{s}\b", msg), msg
    for s in sheet_only:
        assert re.search(rf"sample information only: [^;]*\b{s}\b", msg), msg


def test_countmatrix_lists_many_samples_briefly():
    counts = _counts()
    sheet = _sheet()
    sheet.index = [f"x{i}" for i in range(8)]
    with pytest.raises(SampleMismatchException) as e:
        CountMatrix(counts, sheet)
    msg = str(e.value)
    assert "\n" not in msg
    assert "and 3 more" in msg, msg


def test_countmatrix_matches_a_reorder_by_name():
    counts = _counts()
    mat = CountMatrix(counts, _sheet().iloc[::-1], design="counts ~ batch + condition")
    assert list(mat.counts.columns) == SAMPLES
    assert list(mat.column_data.index) == SAMPLES
    assert list(mat.design_matrix.full_matrix.index) == SAMPLES
    pandas.testing.assert_frame_equal(mat.counts, counts)


def test_countmatrix_strict_still_requires_the_order():
    with pytest.raises(SampleMismatchException, match="same order"):
        CountMatrix(_counts(), _sheet().iloc[::-1], strict=True)
    CountMatrix(_counts(), _sheet(), strict=True)


def test_countmatrix_strict_names_differing_samples():
    with pytest.raises(SampleMismatchException) as e:
        CountMatrix(_counts(), _sheet(SAMPLES[:-1] + ["999"]), strict=True)
    assert re.search(r"counts only: 008\b", str(e.value))


def test_countmatrix_subset_is_explicit():
    # what detk-util tidy asks for: the samples in both, in the counts' order
    mat = CountMatrix(_counts(), _sheet(SAMPLES[:-1] + ["999"]), subset=True)
    assert list(mat.counts.columns) == SAMPLES[:-1]
    assert list(mat.column_data.index) == SAMPLES[:-1]


# ------------------------------------------- every command that takes one

# each command that matches a counts file to a sample information file, run
# with the renamed sheet (<sheet>) and its output (out.csv); the error comes
# before any R is run, so none of these needs R
COMMANDS = [
    pytest.param(
        "detk-de",
        ["deseq2", "counts ~ batch + condition", "counts.csv", "<sheet>"],
        id="detk-de-deseq2",
    ),
    pytest.param(
        "detk-de",
        ["firth", "condition ~ counts", "counts.csv", "<sheet>"],
        id="detk-de-firth",
    ),
    pytest.param(
        "detk-transform",
        ["rlog", "counts.csv", "counts ~ condition", "<sheet>"],
        id="detk-transform-rlog",
    ),
    pytest.param(
        "detk-filter",
        ["mean(condition) > 10", "counts.csv", "<sheet>"],
        id="detk-filter",
    ),
    pytest.param("detk-stats", ["summary", "counts.csv", "<sheet>"], id="detk-stats-summary"),
    pytest.param("detk-stats", ["pca", "counts.csv", "<sheet>"], id="detk-stats-pca"),
    pytest.param(
        "detk-wrapr",
        ["run", "script.R", "counts.csv", "out.csv", "--meta-in", "<sheet>"],
        id="detk-wrapr-run",
    ),
]


def _argv(prog, args, sheet):
    argv = [prog] + [sheet if a == "<sheet>" else a for a in args] + ["--no-report"]
    if "out.csv" not in argv:
        argv += ["-o", "out.csv"]
    return argv


@pytest.mark.parametrize("prog,args", COMMANDS)
def test_command_refuses_differing_samples(work, prog, args):
    (work / "script.R").write_text("write.csv(counts.mat, out.fn)\n")
    outcome = cli_adapter.run(_argv(prog, args, "renamed.csv"))
    assert_mismatch(outcome, prog, work / "out.csv")


@pytest.mark.parametrize("prog,args", COMMANDS)
def test_command_refuses_an_extra_sample_in_the_sheet(work, prog, args):
    (work / "script.R").write_text("write.csv(counts.mat, out.fn)\n")
    outcome = cli_adapter.run(_argv(prog, args, "extra.csv"))
    assert_mismatch(outcome, prog, work / "out.csv", counts_only=(), sheet_only=("009",))


@pytest.mark.parametrize(
    "prog,args",
    [
        pytest.param("detk-filter", ["mean(condition) > 10", "counts.csv", "<sheet>"], id="filter"),
        pytest.param("detk-stats", ["pca", "counts.csv", "<sheet>"], id="stats-pca"),
    ],
)
def test_command_matches_a_reorder(work, prog, args):
    ordered = cli_adapter.run(_argv(prog, args, "samples.csv"))
    assert ordered.code == 0, ordered.stderr
    expected = (work / "out.csv").read_text()
    (work / "out.csv").unlink()
    reordered = cli_adapter.run(_argv(prog, args, "reordered.csv"))
    assert reordered.code == 0, reordered.stderr
    assert (work / "out.csv").read_text() == expected


def test_strict_refuses_a_reorder(work):
    outcome = cli_adapter.run(
        _argv(
            "detk-de",
            ["deseq2", "--strict", "counts ~ batch + condition", "counts.csv", "<sheet>"],
            "reordered.csv",
        )
    )
    assert outcome.code == 1, outcome.stderr
    assert not (work / "out.csv").exists()
    assert re.search(r"^detk-de: error: .*same order", outcome.stderr, re.M), outcome.stderr


# ------------------------------------------------ the audit's case, with R


def _deseq2(sheet):
    return cli_adapter.run(
        _argv("detk-de", ["deseq2", "counts ~ batch + condition", "counts.csv", "<sheet>"], sheet)
    )


@deseq2_test
def test_deseq2_refuses_the_audits_case(work):
    # 1.0.0: exit 0, 7 samples fitted, results written, no warning
    assert_mismatch(_deseq2("renamed.csv"), "detk-de", work / "out.csv")


@deseq2_test
def test_deseq2_reorder_gives_the_ordered_results(work):
    ordered = _deseq2("samples.csv")
    assert ordered.code == 0, ordered.stderr
    expected = pandas.read_csv(work / "out.csv", index_col=0)
    (work / "out.csv").unlink()
    reordered = _deseq2("reordered.csv")
    assert reordered.code == 0, reordered.stderr
    pandas.testing.assert_frame_equal(pandas.read_csv(work / "out.csv", index_col=0), expected)
