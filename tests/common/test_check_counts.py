"The shared count-matrix check, de_toolkit.common.check_counts (release-1-0-1/count-checks, count-checks-readers)"

import io

import pandas
import pytest

from de_toolkit.common import COLUMNS_AS_WRITTEN, CountsError, check_counts, read_id_table


def read(text):
    return read_id_table(io.StringIO(text))


def test_well_formed_counts_pass():
    check_counts(read("gene,A,B\ng1,0,2\ng2,3,0\n"), "c.csv")


def test_read_id_table_keeps_the_header_as_written():
    table = read("gene,A,A,B\ng1,1,2,3\n")
    assert list(table.columns) == ["A", "A.1", "B"]
    assert table.attrs[COLUMNS_AS_WRITTEN] == {"A": "A", "A.1": "A", "B": "B"}


def test_read_id_table_header_without_the_id_field():
    # R's write.table leaves out the header cell over the row names
    table = read("A,A,B\ng1,1,2,3\n")
    assert table.attrs[COLUMNS_AS_WRITTEN] == {"A": "A", "A.1": "A", "B": "B"}
    with pytest.raises(CountsError, match=r"sample 'A' is named more than once"):
        check_counts(table, "c.csv")


@pytest.mark.parametrize("sep", [",", "\t"])
def test_duplicate_header(sep):
    text = sep.join(["gene", "A", "B", "A", "B"]) + "\n" + sep.join(["g1", "1", "2", "3", "4"])
    with pytest.raises(CountsError) as e:
        check_counts(read(text + "\n"), "c.csv")
    assert str(e.value) == (
        "c.csv: sample 'A' is named more than once in the header (sample columns 1 and 3)"
        " (and 1 more repeated sample name)"
    )


def test_a_name_that_pandas_would_give_a_repeat_is_not_a_repeat():
    # 'A.1' written in the header is its own sample
    check_counts(read("gene,A,A.1\ng1,1,2\n"), "c.csv")


def test_duplicate_header_without_attrs_falls_back_to_the_columns():
    counts = pandas.DataFrame([[1, 2]], index=["g1"], columns=["A", "A"])
    with pytest.raises(CountsError, match=r"^counts: sample 'A' .*\(sample columns 1 and 2\)$"):
        check_counts(counts)


def test_duplicate_feature():
    with pytest.raises(CountsError) as e:
        check_counts(read("gene,A\ng2,1\ng1,1\ng2,1\ng1,1\n"), "c.csv")
    assert str(e.value) == (
        "c.csv: feature 'g2' is listed more than once (feature rows 1 and 3)"
        " (and 1 more repeated feature ID)"
    )


def test_feature_ids_are_compared_as_written():
    # 007 and 7 are different IDs
    check_counts(read("gene,A\n007,1\n7,1\n"), "c.csv")


def test_negative_count_names_a_fractional_value():
    with pytest.raises(
        CountsError, match=r"feature 'g2' in sample 'B' has a negative count, -0.5$"
    ):
        check_counts(read("gene,A,B\ng1,1,2\ng2,3,-0.5\n"), "c.csv")


def test_zero_depth():
    with pytest.raises(CountsError) as e:
        check_counts(read("gene,A,B,C\ng1,0,1,0\ng2,0,1,0\n"), "c.csv")
    assert str(e.value) == (
        "c.csv: sample 'A' has no counts: its counts sum to 0 (and 1 more zero-depth sample)"
    )


def test_checks_run_in_order():
    # a repeated header is reported before a repeated feature, a negative
    # count or a zero-depth sample
    with pytest.raises(CountsError, match="named more than once"):
        check_counts(read("gene,A,A\ng1,-1,0\ng1,1,0\n"), "c.csv")
    with pytest.raises(CountsError, match="listed more than once"):
        check_counts(read("gene,A,B\ng1,-1,0\ng1,1,0\n"), "c.csv")
    with pytest.raises(CountsError, match="negative count"):
        check_counts(read("gene,A,B\ng1,-1,0\ng2,1,0\n"), "c.csv")


def test_counts_error_is_a_value_error():
    assert issubclass(CountsError, ValueError)


# a subset or reordering of the columns, as CountMatrix makes with column
# data (counts[common_names]), keeps each sample's name as written


@pytest.mark.parametrize("cols", [["B", "C"], ["C", "B"]])
def test_negative_count_after_selecting_columns(cols):
    table = read("gene,A,B,C\ng1,1,-2,3\ng2,0,5,6\n")
    with pytest.raises(CountsError, match=r"in sample 'B' has a negative count, -2$"):
        check_counts(table[cols], "c.csv")


@pytest.mark.parametrize("cols", [["B", "C"], ["C", "B"]])
def test_zero_depth_after_selecting_columns(cols):
    table = read("gene,A,B,C\ng1,1,2,0\ng2,1,5,0\n")
    with pytest.raises(CountsError, match=r"^c.csv: sample 'C' has no counts"):
        check_counts(table[cols], "c.csv")


def test_selection_without_the_offending_samples_passes():
    table = read("gene,A,B,C\ng1,-1,2,3\ng2,0,5,6\n")
    check_counts(table[["C", "B"]], "c.csv")


def test_a_repeated_name_that_survives_the_selection():
    table = read("gene,A,A,B\ng1,1,2,3\n")
    with pytest.raises(CountsError) as e:
        check_counts(table[["B", "A.1", "A"]], "c.csv")
    assert str(e.value) == (
        "c.csv: sample 'A' is named more than once in the header (sample columns 2 and 3)"
    )


def test_a_repeated_name_that_does_not_survive_the_selection():
    table = read("gene,A,A,B\ng1,1,2,3\n")
    check_counts(table[["A", "B"]], "c.csv")
    check_counts(table[["A.1", "B"]], "c.csv")


def test_check_after_count_matrix_lines_up_column_data():
    from de_toolkit.common import CountMatrix

    counts = read("gene,A,B,C\ng1,1,-2,3\ng2,0,5,6\n")
    column_data = read("sample,cond\nC,x\nB,y\nA,z\n")
    cm = CountMatrix(counts, column_data=column_data)
    with pytest.raises(CountsError, match=r"in sample 'B' has a negative count, -2$"):
        check_counts(cm.counts, "c.csv")


# values=False: only the repeated header and feature checks, for a command
# that may take a normalized or transformed matrix (DETK-0830)


def test_values_false_passes_negative_and_zero_depth():
    check_counts(read("gene,A,B\ng1,-1.5,0\ng2,2.5,0\n"), "c.csv", values=False)
    check_counts(read("gene,A,B\ng1,NA,x\ng2,NA,y\n"), "c.csv", values=False)


@pytest.mark.parametrize(
    "text,match",
    [
        ("gene,A,A\ng1,-1,0\ng2,1,0\n", "named more than once"),
        ("gene,A,B\ng1,-1,0\ng1,1,0\n", "listed more than once"),
    ],
)
def test_values_false_still_rejects_repeated_ids(text, match):
    with pytest.raises(CountsError, match=match):
        check_counts(read(text), "c.csv", values=False)


# a sample with no numeric value is not reported as zero depth (#196 review)


@pytest.mark.parametrize("column", ["NA,NA", "x,y", "NA,y"])
def test_sample_with_no_numeric_value(column):
    a, b = column.split(",")
    with pytest.raises(CountsError) as e:
        check_counts(read(f"gene,A,B\ng1,{a},1\ng2,{b},2\n"), "c.csv")
    assert str(e.value) == (
        "c.csv: sample 'A' has no numeric counts: its values are all missing or not numbers"
    )


def test_a_sample_with_some_numeric_values_is_checked_by_its_sum():
    with pytest.raises(CountsError, match="'A' has no counts: its counts sum to 0"):
        check_counts(read("gene,A,B\ng1,NA,1\ng2,0,2\n"), "c.csv")


# CountMatrixFile(check=...) checks the counts as read, before the column data
# selects or reorders a sample (DETK-0830)


def write(tmp_path, counts, column_data="sample,cond\nC,x\nB,y\nA,y\n"):
    (tmp_path / "c.csv").write_text(counts)
    (tmp_path / "cd.csv").write_text(column_data)
    return str(tmp_path / "c.csv"), str(tmp_path / "cd.csv")


def test_count_matrix_file_finds_a_repeat_the_column_data_drops(tmp_path):
    from de_toolkit.common import CountMatrixFile

    counts, column_data = write(tmp_path, "gene,A,A,B,C\ng1,1,2,3,4\ng2,5,6,7,8\n")
    # 1.0.0, and check=None: the column data names A, so A.1 is dropped
    assert list(CountMatrixFile(counts, column_data).counts.columns) == ["A", "B", "C"]
    with pytest.raises(CountsError) as e:
        CountMatrixFile(counts, column_data, check="ids")
    # positions in the file, though the column data lists C, B, A
    assert str(e.value) == (
        f"{counts}: sample 'A' is named more than once in the header (sample columns 1 and 2)"
    )


@pytest.mark.parametrize("check,raises", [(None, False), ("ids", False), ("raw", True)])
def test_count_matrix_file_check_values(tmp_path, check, raises):
    from de_toolkit.common import CountMatrixFile

    counts, column_data = write(tmp_path, "gene,A,B,C\ng1,1,-2,3\ng2,4,5,6\n")
    if raises:
        with pytest.raises(CountsError, match="in sample 'B' has a negative count, -2$"):
            CountMatrixFile(counts, column_data, check=check)
    else:
        CountMatrixFile(counts, column_data, check=check)


def test_count_matrix_file_check_must_be_known(tmp_path):
    from de_toolkit.common import CountMatrixFile

    counts, _ = write(tmp_path, "gene,A,B\ng1,1,2\n")
    with pytest.raises(ValueError, match="check must be None, 'ids' or 'raw'"):
        CountMatrixFile(counts, check="all")
