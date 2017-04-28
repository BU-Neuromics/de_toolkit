import docopt
import pytest
from de_toolkit.common import main

def test_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_CountMatrix(
  fake_counts_pandas_dataframe
  ,fake_column_data_pandas_dataframe
  ) :

  from de_toolkit import CountMatrix

  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,index=None
    ,columns=None
    ,column_data=fake_column_data_pandas_dataframe
  )

def test_CountMatrixFile() :
  from de_toolkit import CountMatrixFile
  assert False
