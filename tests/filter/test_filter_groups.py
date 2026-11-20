"""
A filter expression's group, as in cond[Z], selects the samples whose value
in the column is the group as written: a number for a column of numbers, true
or false for a column of booleans, text otherwise. A group the column does not
have is a usage error (exit 2) naming the column, the group and the values
present, and no output is written (release/parse-errors).
"""

import warnings

import pytest

from de_toolkit.filter import main

COUNTS = "gene,s1,s2,s3,s4\ng1,10,20,30,40\ng2,5,0,15,25\n"
COV = "sample,cond,flag,dose,b\ns1,A,0,0.5,True\ns2,A,1,0.5,False\ns3,B,0,2,TRUE\ns4,B,1,2,false\n"


@pytest.fixture
def files(tmp_path, monkeypatch):
    (tmp_path / "counts.csv").write_text(COUNTS)
    (tmp_path / "cov.csv").write_text(COV)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run(command):
    main(["detk-filter", "--no-report", "-o", "out.csv", command, "counts.csv", "cov.csv"])


def kept(files):
    return [line.split(",")[0] for line in (files / "out.csv").read_text().splitlines()[1:]]


@pytest.mark.parametrize(
    "command, genes",
    [
        # g1's mean is 15 in A and 35 in B, g2's 2.5 and 20
        ("mean(cond[A]) > 12", ["g1"]),
        ("mean(cond[B]) > 12", ["g1", "g2"]),
        # a 0/1 column: s2 and s4 (g1 30, g2 12.5)
        ("mean(flag[1]) > 12", ["g1", "g2"]),
        ("mean(flag[1]) > 20", ["g1"]),
        ("mean(flag[0]) > 12", ["g1"]),
        # a column of decimals: s1 and s2
        ("mean(dose[0.5]) > 12", ["g1"]),
        ("mean(dose[2]) > 12", ["g1", "g2"]),
        # a column of booleans, in any case: True is s1 and s3 (g1 20, g2 10)
        ("mean(b[true]) > 12", ["g1"]),
        ("mean(b[TRUE]) > 12", ["g1"]),
        ("mean(b[False]) > 12", ["g1", "g2"]),
    ],
)
def test_group_selects_its_samples(files, command, genes):
    run(command)
    assert kept(files) == genes


@pytest.mark.parametrize(
    "command, message",
    [
        (
            "mean(cond[Z]) > 1",
            "the filter expression names the group 'Z' of the column 'cond', "
            "which has no such value (its values: A, B)",
        ),
        (
            "mean(flag[3]) > 1",
            "the filter expression names the group '3' of the column 'flag', "
            "which has no such value (its values: 0, 1)",
        ),
        (
            "mean(dose[1]) > 1",
            "the filter expression names the group '1' of the column 'dose', "
            "which has no such value (its values: 0.5, 2.0)",
        ),
        (
            "mean(b[yes]) > 1",
            "the filter expression names the group 'yes' of the column 'b', "
            "which has no such value (its values: False, True)",
        ),
        # in either clause of a compound expression
        (
            "mean(all) > 1 and nonzero(cond[a]) > 0",
            "the filter expression names the group 'a' of the column 'cond', "
            "which has no such value (its values: A, B)",
        ),
    ],
)
def test_group_not_in_its_column_is_a_usage_error(files, capsys, command, message):
    with warnings.catch_warnings():
        # the group no longer warns, it stops the run
        warnings.simplefilter("error", UserWarning)
        with pytest.raises(SystemExit) as e:
            run(command)
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert f"detk-filter: error: {message}\n" in err
    assert not (files / "out.csv").exists()
