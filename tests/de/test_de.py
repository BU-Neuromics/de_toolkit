import docopt
import pytest
from de_toolkit.de import main

def test_de_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_firth_cli(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ ',fake_counts_csv,fake_column_data_csv])

def test_firth_cli_w_cov(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ cont_cov',fake_counts_csv,fake_column_data_csv])

def test_firth(fake_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_counts_obj.add_design('category ~')

  firth_out = firth_logistic_regression(fake_counts_obj)

def test_firth_w_cov(fake_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_counts_obj.add_design('category ~ cont_cov')

  firth_out = firth_logistic_regression(fake_counts_obj)

# these tests take a long time, only do them if necessary
#def test_firth_w_big_data_cov(fake_big_counts_obj) :
#  from de_toolkit.de import firth_logistic_regression
#
#  fake_big_counts_obj.add_design('category ~ cont_cov')
#
#  firth_out = firth_logistic_regression(fake_big_counts_obj)

#def test_firth_w_huge_data_cov(fake_huge_counts_obj) :
#  from de_toolkit.de import firth_logistic_regression
#
#  fake_huge_counts_obj.add_design('category ~ cont_cov')
#
#  firth_out = firth_logistic_regression(fake_huge_counts_obj)

def test_firth_w_bad_cov(fake_counts_obj) :
  from de_toolkit.de import firth_logistic_regression
  from de_toolkit.common import InvalidDesignException

  fake_counts_obj.add_design('category ~ cont_covx')

  with pytest.raises(InvalidDesignException) :
    firth_out = firth_logistic_regression(fake_counts_obj)


# for issue #4, "no memory available" in logistf.c is caused by improper
# handling of an empty sample name intersection between counts and covs,
# case covered in common/test_common.py


# tests for:
#   - profile likelihood estimation crash (issue #3)
def test_firth_bad_counts() :
  import os
  import pandas
  from de_toolkit.common import CountMatrix
  from de_toolkit.de import firth_logistic_regression

  base_dir = os.path.join('tests','de')

  # bad_counts.csv contains real gene data that have been found to give
  # Firth difficulty, in order:
  #   1. gene is fine
  #   2. gene crashes on the profile likelihood method, and so reverts to Wald
  counts = pandas.read_csv(
    os.path.join(base_dir,'bad_counts.csv')
    ,index_col=0
  )
  cov = pandas.read_csv(
    os.path.join(base_dir,'sample_info__batch_PD3.csv')
    ,index_col=1
  )

  mat = CountMatrix(
    counts
    ,column_data=cov
    ,design='Condition ~'
  )

  firth_out = firth_logistic_regression(mat)

  assert firth_out.status[0] == 'PL'
  assert firth_out.status[1] == 'Wald'

