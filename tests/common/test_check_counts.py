"The shared count-matrix check, de_toolkit.common.check_counts (release-1-0-1/count-checks)"

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
    assert table.attrs[COLUMNS_AS_WRITTEN] == ["A", "A", "B"]


def test_read_id_table_header_without_the_id_field():
    # R's write.table leaves out the header cell over the row names
    table = read("A,A,B\ng1,1,2,3\n")
    assert table.attrs[COLUMNS_AS_WRITTEN] == ["A", "A", "B"]
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
