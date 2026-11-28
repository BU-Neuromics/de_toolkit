"""
Every command that reads a counts matrix runs the count checks
(release-1-0-1/count-checks-readers, DETK-0830).

On v1.0.0 every command below accepted a counts file that names a sample
twice in its header ('gene,A,A,B,C', which pandas reads as A, A.1, B, C) or
lists a feature twice. It went on with A.1 as a sample of its own, or, when
column data names A, B and C, dropped A.1 without a word; and it kept both
rows of the repeated feature. Now each exits 1 (DETK-0601: a bad input
file) before any R step, output or report, and prints one stderr line
naming the offender.

Negative counts and zero-depth samples are rejected only by the commands
that need raw counts (detk-norm deseq2, library, cpm, fpkm, tpm; detk-de
deseq2; detk-transform vst, rlog). The commands that may take a normalized
or transformed matrix (detk-de firth, detk-transform plog, detk-stats,
detk-filter, detk-outlier) accept them. docs/concepts.md lists the split.
"""

import importlib

import pytest

HINT = " (--verbose for the traceback)"

DUP_HEADER = "gene,A,A,B,C\ng1,1,2,3,4\ng2,5,6,7,8\ng3,9,10,11,12\n"
DUP_FEATURE = "gene,A,B,C\ng1,1,2,3\ng1,4,5,6\ng2,7,8,9\n"
NEGATIVE = "gene,A,B,C\ng1,1,-2,3\ng2,4,5,6\ng3,7,8,9\n"
ZERO_DEPTH = "gene,A,B,C\ng1,1,0,3\ng2,4,0,6\ng3,7,0,9\n"
# a transformed matrix holds decimals (and detk-outlier shrink, on 1.0.0
# and here, fails on a matrix of integers, a separate bug)
TRANSFORMED_OK = "gene,A,B,C\ng1,1.5,2.5,3.5\ng2,4.5,5.5,6.5\ng3,7.5,8.5,9.5\n"
TRANSFORMED_NEGATIVE = "gene,A,B,C\ng1,1.5,-2.5,3.5\ng2,4.5,5.5,6.5\ng3,7.5,8.5,9.5\n"
TRANSFORMED_ZERO = "gene,A,B,C\ng1,1.5,0.0,3.5\ng2,4.5,0.0,6.5\ng3,7.5,0.0,9.5\n"
COLUMN_DATA = "sample,cond\nA,x\nB,y\nC,y\n"
LENGTHS = "gene,length\ng1,1000\ng2,2000\ng3,3000\n"

DUP_HEADER_MSG = (
    "counts.csv: sample 'A' is named more than once in the header (sample columns 1 and 2)"
)
DUP_FEATURE_MSG = "counts.csv: feature 'g1' is listed more than once (feature rows 1 and 2)"
NEGATIVE_MSG = "counts.csv: feature 'g1' in sample 'B' has a negative count, -2"
ZERO_DEPTH_MSG = "counts.csv: sample 'B' has no counts: its counts sum to 0"

# (command, module, argv after the program name); every argv reads
# counts.csv, and those with column data read cov.csv, which names A, B, C
RAW = {
    "norm deseq2": ("norm", ["deseq2", "counts.csv"]),
    "norm library": ("norm", ["library", "counts.csv"]),
    "norm cpm": ("norm", ["cpm", "counts.csv"]),
    "norm fpkm": ("norm", ["fpkm", "counts.csv", "lengths.csv"]),
    "norm tpm": ("norm", ["tpm", "counts.csv", "lengths.csv"]),
    "de deseq2": ("de", ["deseq2", "counts ~ cond", "counts.csv", "cov.csv"]),
    "transform vst": ("transform", ["vst", "counts.csv"]),
    "transform rlog": ("transform", ["rlog", "counts.csv"]),
    "transform rlog with column data": (
        "transform",
        ["rlog", "counts.csv", "counts ~ cond", "cov.csv"],
    ),
}
TRANSFORMED = {
    "de firth": ("de", ["firth", "cond ~ counts", "counts.csv", "cov.csv"]),
    "transform plog": ("transform", ["plog", "counts.csv"]),
    **{
        f"stats {sub}": ("stats", [sub, "counts.csv"])
        for sub in (
            "summary",
            "basestats",
            "coldist",
            "rowdist",
            "colzero",
            "rowzero",
            "entropy",
            "pca",
        )
    },
    "stats summary with column data": ("stats", ["summary", "counts.csv", "cov.csv"]),
    "filter": ("filter", ["mean(all) > -100", "counts.csv"]),
    "filter with column data": ("filter", ["mean(cond) > -100", "counts.csv", "cov.csv"]),
    "outlier entropy": ("outlier", ["entropy", "-p", "0.05", "counts.csv"]),
    "outlier shrink": ("outlier", ["shrink", "counts.csv"]),
}
ALL = {**RAW, **TRANSFORMED}


def run(command, counts, tmp_path, monkeypatch):
    "run *command* on *counts* in tmp_path; its exit code (0 on return)"
    module, argv = ALL[command]
    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text(counts)
    (tmp_path / "cov.csv").write_text(COLUMN_DATA)
    (tmp_path / "lengths.csv").write_text(LENGTHS)
    main = importlib.import_module(f"de_toolkit.{module}").main
    try:
        main([f"detk-{module}", *argv, "--no-report", "-o", "out.csv"])
    except SystemExit as e:
        return e.code
    return 0


def assert_rejected(command, counts, message, tmp_path, monkeypatch, capsys):
    module = ALL[command][0]
    assert run(command, counts, tmp_path, monkeypatch) == 1
    # nothing written
    assert not (tmp_path / "out.csv").exists()
    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [f"detk-{module}: error: {message}{HINT}"]


@pytest.mark.parametrize("command", list(ALL))
def test_duplicate_sample_header_exits_1(command, tmp_path, monkeypatch, capsys):
    assert_rejected(command, DUP_HEADER, DUP_HEADER_MSG, tmp_path, monkeypatch, capsys)


@pytest.mark.parametrize("command", list(ALL))
def test_duplicate_feature_id_exits_1(command, tmp_path, monkeypatch, capsys):
    assert_rejected(command, DUP_FEATURE, DUP_FEATURE_MSG, tmp_path, monkeypatch, capsys)


@pytest.mark.parametrize("command", list(RAW))
def test_raw_count_commands_reject_a_negative_count(command, tmp_path, monkeypatch, capsys):
    assert_rejected(command, NEGATIVE, NEGATIVE_MSG, tmp_path, monkeypatch, capsys)


@pytest.mark.parametrize("command", list(RAW))
def test_raw_count_commands_reject_a_zero_depth_sample(command, tmp_path, monkeypatch, capsys):
    assert_rejected(command, ZERO_DEPTH, ZERO_DEPTH_MSG, tmp_path, monkeypatch, capsys)


# firth needs R; the others run here
TRANSFORMED_PY = [c for c in TRANSFORMED if c != "de firth"]


@pytest.mark.parametrize(
    "counts", [TRANSFORMED_NEGATIVE, TRANSFORMED_ZERO], ids=["negative", "zero-depth"]
)
@pytest.mark.parametrize("command", TRANSFORMED_PY)
def test_transformed_matrix_commands_accept_negative_and_zero_depth(
    command, counts, tmp_path, monkeypatch, capsys
):
    code = run(command, counts, tmp_path, monkeypatch)
    err = capsys.readouterr().err
    assert "negative count" not in err and "has no counts" not in err
    assert code == 0, err
    assert (tmp_path / "out.csv").exists()


@pytest.mark.parametrize("command", TRANSFORMED_PY)
def test_transformed_matrix_commands_still_run_on_good_counts(command, tmp_path, monkeypatch):
    assert run(command, TRANSFORMED_OK, tmp_path, monkeypatch) == 0
    assert (tmp_path / "out.csv").exists()
