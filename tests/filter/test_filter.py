import docopt
import pytest
import pandas as pd
from de_toolkit.filter import *
from de_toolkit.common import *

def test_filter_nonzero_fraction_lt(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 0.5, '<')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_nonzero_fraction_lte(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 1/3, '<=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_nonzero_fraction_gt(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 0.5, '>')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_nonzero_fraction_gte(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2/3, '>=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_nonzero_fraction_e(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2/3, '=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    assert true_df.equals(output)

def test_filter_nonzero_int_lt(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2, '<')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_nonzero_int_lte(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2, '<=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    assert true_df.equals(output)

def test_filter_nonzero_int_gt(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2, '>')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_nonzero_int_gte(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2, '>=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_nonzero_int_e(fake_counts_obj_with_zeros):
    output = filter_nonzero(fake_counts_obj_with_zeros, 2, '=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    assert true_df.equals(output)

def test_filter_zero_fraction_lt(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 0.5, '<')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_zero_fraction_lte(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 1/3, '<=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_zero_fraction_gt(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 0.5, '>')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_zero_fraction_gte(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 2/3, '>=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_zero_fraction_e(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 1/3, '=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    assert true_df.equals(output)

def test_filter_zero_int_lt(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 2, '<')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_zero_int_lte(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 2, '<=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_zero_int_gt(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 1, '>')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_zero_int_gte(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 1, '>=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    assert true_df.equals(output)

def test_filter_zero_int_e(fake_counts_obj_with_zeros):
    output = filter_zeros(fake_counts_obj_with_zeros, 1, '=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    assert true_df.equals(output)

def test_filter_mean_lt(fake_counts_obj_with_zeros):
    output = filter_mean(fake_counts_obj_with_zeros, 3, '<')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_mean_lte(fake_counts_obj_with_zeros):
    output = filter_mean(fake_counts_obj_with_zeros, 3, '<=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_mean_gt(fake_counts_obj_with_zeros):
    output = filter_mean(fake_counts_obj_with_zeros, 3, '>')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_mean_gte(fake_counts_obj_with_zeros):
    output = filter_mean(fake_counts_obj_with_zeros, 3, '>=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_mean_e(fake_counts_obj_with_zeros):
    output = filter_mean(fake_counts_obj_with_zeros, 3, '=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    assert true_df.equals(output)

def test_filter_median_lt(fake_counts_obj_with_zeros):
    output = filter_median(fake_counts_obj_with_zeros, 2, '<')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_median_lte(fake_counts_obj_with_zeros):
    output = filter_median(fake_counts_obj_with_zeros, 2, '<=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene2'] = [0.0, 9.0, 0.0]
    true_df.loc['gene3'] = [4.0, 0.0, 0.0]
    assert true_df.equals(output)

def test_filter_median_gt(fake_counts_obj_with_zeros):
    output = filter_median(fake_counts_obj_with_zeros, 2, '>')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_median_gte(fake_counts_obj_with_zeros):
    output = filter_median(fake_counts_obj_with_zeros, 2, '>=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    true_df.loc['gene4'] = [5.0, 0.0, 125.0]
    true_df.loc['gene5'] = [6.0, 36.0, 216.0]
    assert true_df.equals(output)

def test_filter_median_e(fake_counts_obj_with_zeros):
    output = filter_median(fake_counts_obj_with_zeros, 2, '=')
    true_df = pd.DataFrame(columns=['a', 'b', 'c'])
    true_df.loc['gene1'] = [2.0, 4.0, 0.0]
    assert true_df.equals(output)
