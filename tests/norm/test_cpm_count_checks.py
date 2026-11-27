"""
detk-norm cpm rejects a malformed counts file (release-1-0-1/count-checks).

On v1.0.0 each of these counts files exited 0 with a wrong answer:

- 'gene,A,A,B': pandas renamed the second A, so the output had columns
  A, A.1, B
- two rows of g1: both were normalized, and the output had two g1 rows
- a count of -1: its CPM was negative (-250000.0)
- sample A all zero: its column of CPMs was blank (NaN)

Now each exits 1 (DETK-0601: a bad input file, as DETK-0031 says), writes
no output file and no report, and prints one line on stderr naming the
header, feature, sample or value at fault.
"""

import pytest

from de_toolkit.norm import main

HINT = " (--verbose for the traceback)"

CASES = {
    "duplicate-header": (
        "gene,A,A,B\ng1,1,2,3\ng2,4,5,6\n",
        "counts.csv: sample 'A' is named more than once in the header (fields 2 and 3)",
    ),
    "duplicate-feature": (
        "gene,A,B\ng1,1,2\ng1,3,4\ng2,5,6\n",
        "counts.csv: feature 'g1' is listed more than once (lines 2 and 3)",
    ),
    "negative-count": (
        "gene,A,B\ng1,-1,2\ng2,5,6\n",
        "counts.csv: feature 'g1' in sample 'A' has a negative count, -1",
    ),
    "zero-depth": (
        "gene,A,B\ng1,0,2\ng2,0,6\n",
        "counts.csv: sample 'A' has no counts: its counts sum to 0",
    ),
}


@pytest.mark.parametrize("case", list(CASES))
def test_cpm_rejects_malformed_counts(case, tmp_path, monkeypatch, capsys):
    text, message = CASES[case]
    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text(text)
    with pytest.raises(SystemExit) as exc:
        main(["detk-norm", "cpm", "-o", "out.csv", "counts.csv"])
    assert exc.value.code == 1
    # no output file and no report
    assert sorted(p.name for p in tmp_path.iterdir()) == ["counts.csv"]
    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [f"detk-norm: error: {message}{HINT}"]


def test_cpm_names_how_many_more_offenders(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text("gene,A,B,C\ng1,-1,-2,3\ng2,5,-6,7\n")
    with pytest.raises(SystemExit) as exc:
        main(["detk-norm", "cpm", "-o", "out.csv", "counts.csv"])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert err.splitlines() == [
        "detk-norm: error: counts.csv: feature 'g1' in sample 'A' has a negative count, -1"
        f" (and 2 more negative counts){HINT}"
    ]


def test_cpm_well_formed_counts_still_normalize(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text("gene,A,B\ng1,1,3\ng2,3,1\n")
    main(["detk-norm", "cpm", "--no-report", "-o", "out.csv", "counts.csv"])
    assert (tmp_path / "out.csv").read_text().splitlines() == [
        "gene,A,B",
        "g1,250000.0,750000.0",
        "g2,750000.0,250000.0",
    ]
