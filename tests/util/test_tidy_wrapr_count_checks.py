"""
detk-util tidy, tidy-counts, tidy-covs and detk-wrapr run reject a counts
file with a repeated sample header or feature ID
(release-1-0-1/tidy-wrapr-checks, DETK-0850).

On v1.0.0, 'detk-util tidy-counts' given 'gene,A,A,B,C' and column data
naming A, B and C exited 0 and wrote 'gene,A,B,C': pandas read the second A
as 'A.1', which the column data does not name, so it was dropped without a
word. A feature ID listed twice went through as two rows. 'detk-util tidy',
'tidy-covs' and 'detk-wrapr run' did the same.

Now each exits 1 (DETK-0601), writes no output and prints one line on
stderr naming the repeated header or feature. These commands may take a
normalized or transformed matrix, so they run the repeated-ID checks only
(check_counts with values=False, DETK-0830): a negative count and a
zero-depth sample are still accepted.
"""

import pandas
import pytest

from de_toolkit import util, wrapr

HINT = " (--verbose for the traceback)"

SHEET = "sample,condition\nA,a\nB,b\nC,c\n"

DUPLICATES = {
    "duplicate-header": (
        "gene,A,A,B,C\ng1,1,2,3,4\ng2,5,6,7,8\n",
        "counts.csv: sample 'A' is named more than once in the header (sample columns 1 and 2)",
    ),
    "duplicate-feature": (
        "gene,A,B,C\ng1,1,2,3\ng1,4,5,6\ng2,7,8,9\n",
        "counts.csv: feature 'g1' is listed more than once (feature rows 1 and 2)",
    ),
}

TIDY_COMMANDS = ["tidy", "tidy-counts", "tidy-covs"]


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "samples.csv").write_text(SHEET)
    return tmp_path


def _assert_rejected(exc, capsys, work, prog, message, inputs):
    assert exc.value.code == 1
    # no output file and no report
    assert sorted(p.name for p in work.iterdir()) == sorted(inputs)
    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [f"{prog}: error: {message}{HINT}"]


def test_tidy_counts_no_longer_drops_a_repeated_sample(work, capsys):
    # the audit's case: on v1.0.0 this exited 0 and wrote gene,A,B,C
    (work / "counts.csv").write_text(DUPLICATES["duplicate-header"][0])
    with pytest.raises(SystemExit) as exc:
        util.main(["detk-util", "tidy-counts", "-o", "out.csv", "counts.csv", "samples.csv"])
    _assert_rejected(
        exc,
        capsys,
        work,
        "detk-util",
        DUPLICATES["duplicate-header"][1],
        ["counts.csv", "samples.csv"],
    )


@pytest.mark.parametrize("case", list(DUPLICATES))
@pytest.mark.parametrize("command", TIDY_COMMANDS)
def test_tidy_rejects_repeated_ids(command, case, work, capsys):
    text, message = DUPLICATES[case]
    (work / "counts.csv").write_text(text)
    with pytest.raises(SystemExit) as exc:
        util.main(["detk-util", command, "-o", "out.csv", "counts.csv", "samples.csv"])
    _assert_rejected(exc, capsys, work, "detk-util", message, ["counts.csv", "samples.csv"])


@pytest.mark.parametrize("case", list(DUPLICATES))
def test_wrapr_run_rejects_repeated_ids(case, work, capsys, monkeypatch):
    # the check comes before R is looked for or run, so this needs no R
    text, message = DUPLICATES[case]
    (work / "counts.csv").write_text(text)
    (work / "script.R").write_text("write.csv(counts.mat, out.fn)\n")
    monkeypatch.setattr(wrapr, "WrapR", _refuse_to_run)
    with pytest.raises(SystemExit) as exc:
        wrapr.main(["detk-wrapr", "run", "script.R", "counts.csv", "out.csv"])
    _assert_rejected(
        exc, capsys, work, "detk-wrapr", message, ["counts.csv", "samples.csv", "script.R"]
    )


def _refuse_to_run(*args, **kwargs):
    raise AssertionError("WrapR was reached with a malformed counts file")


# ------------------------------------------- values are not checked here

# a negative count (A) and a zero-depth sample (B): a normalized or
# transformed matrix may hold either
VALUES = "gene,A,B,C\ng1,-1.5,0,3\ng2,2.5,0,4\n"


@pytest.mark.parametrize("command", ["tidy", "tidy-counts"])
def test_tidy_still_accepts_negative_and_zero_depth_counts(command, work):
    (work / "counts.csv").write_text(VALUES)
    util.main(["detk-util", command, "--no-report", "-o", "out.csv", "counts.csv", "samples.csv"])
    assert (work / "out.csv").read_text().splitlines() == VALUES.splitlines()


def test_tidy_covs_still_accepts_negative_and_zero_depth_counts(work):
    (work / "counts.csv").write_text(VALUES)
    util.main(
        ["detk-util", "tidy-covs", "--no-report", "-o", "out.csv", "counts.csv", "samples.csv"]
    )
    assert (work / "out.csv").read_text().splitlines() == SHEET.splitlines()


def test_wrapr_run_still_accepts_negative_and_zero_depth_counts(work, monkeypatch):
    (work / "counts.csv").write_text(VALUES)
    (work / "script.R").write_text("write.csv(counts.mat, out.fn)\n")
    seen = {}

    class FakeWrapR:
        def __init__(self, rscript, counts, column_data, **kwargs):
            seen["counts"] = counts

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self):
            pass

    monkeypatch.setattr(wrapr, "WrapR", FakeWrapR)
    wrapr.main(["detk-wrapr", "run", "script.R", "counts.csv", "out.csv"])
    expected = pandas.DataFrame(
        {"A": [-1.5, 2.5], "B": [0, 0], "C": [3, 4]}, index=pandas.Index(["g1", "g2"])
    )
    pandas.testing.assert_frame_equal(seen["counts"], expected, check_names=False)
