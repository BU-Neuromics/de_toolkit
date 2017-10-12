import docopt
import pytest
import pandas as pd
from de_toolkit.filter import *
from de_toolkit.common import *

def test_filter_nonzero_default(fake_counts_obj_with_zeros):
	output = filter_nonzero(fake_counts_obj_with_zeros)
	true_df = pd.DataFrame(columns=['a', 'b', 'c'])
	true_df.loc['gene1'] = [2.0, 4.0, 0.0]
	true_df.loc['gene4'] = [5.0, 0.0, 125.0]
	true_df.loc['gene5'] = [6.0, 36.0, 216.0]
	assert true_df.equals(output)

def test_filter_nonzero_fraction(fake_counts_obj_with_zeros):
	output = filter_nonzero(fake_counts_obj_with_zeros, n=0.7)
	true_df = pd.DataFrame(columns=['a', 'b', 'c'])
	true_df.loc['gene5'] = [6.0, 36.0, 216.0]
	assert true_df.equals(output)

def test_filter_nonzero_number(fake_counts_obj_with_zeros):
	output = filter_nonzero(fake_counts_obj_with_zeros, n=2)
	true_df = pd.DataFrame(columns=['a', 'b', 'c'])
	true_df.loc['gene1'] = [2.0, 4.0, 0.0]
	true_df.loc['gene4'] = [5.0, 0.0, 125.0]
	true_df.loc['gene5'] = [6.0, 36.0, 216.0]
	assert true_df.equals(output)
