import docopt
import pytest
from de_toolkit.de import main

def test_de_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_firth_cli(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ ',fake_counts_csv,fake_column_data_csv])
def test_firth(fake_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_counts_obj.add_design('category ~')

  firth_logistic_regression(fake_counts_obj)
  lkjlakj
