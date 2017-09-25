import docopt
import pytest
from de_toolkit.de import main

def test_de_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_firth_cli(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ counts',fake_counts_csv,fake_column_data_csv])

def test_firth_cli_w_cov(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ cont_cov + counts',fake_counts_csv,fake_column_data_csv])

def test_firth(fake_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_counts_obj.design = 'category ~ counts'

  firth_out = firth_logistic_regression(fake_counts_obj)

def test_firth_w_cov(fake_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_counts_obj.design = 'category ~ cont_cov + counts'

  firth_out = firth_logistic_regression(fake_counts_obj)

def test_firth_w_big_data_cov(fake_big_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_big_counts_obj.design = 'category ~ cont_cov + counts'

  firth_out = firth_logistic_regression(fake_big_counts_obj)

# this test takes a long time, only do it if necessary
#def test_firth_w_huge_data_cov(fake_huge_counts_obj) :
#  from de_toolkit.de import firth_logistic_regression
#
#  fake_huge_counts_obj.add_design('category ~ cont_cov')
#
#  firth_out = firth_logistic_regression(fake_huge_counts_obj)
