import docopt
import pytest
from de_toolkit.common import main, InvalidDesignException

def test_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main()

def test_cli_version() :
    from io import StringIO
    import sys
    oldstdout = sys.stdout
    sys.stdout = StringIO()

    main(['detk','--version'])

    from de_toolkit.common import __version__
    assert sys.stdout.value.strip() == __version__

    sys.stdout = oldstdout

def test_CountMatrix(
  fake_counts_pandas_dataframe
  ,fake_column_data_pandas_dataframe
  ) :

  from de_toolkit import CountMatrix
  from de_toolkit.common import SampleMismatchException

  # with no column data
  mat = CountMatrix(
    fake_counts_pandas_dataframe
  )

  # with column data
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,column_data=fake_column_data_pandas_dataframe
  )
  assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
  assert all(mat.feature_names == fake_counts_pandas_dataframe.index)

  # with column data and design
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,column_data=fake_column_data_pandas_dataframe
    ,design='cont_cov ~ category[case] + counts'
  )
  print(mat.column_data.columns)
  assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
  assert all(mat.feature_names == fake_counts_pandas_dataframe.index)
  assert mat.design == 'cont_cov ~ Intercept + category__cont + counts'

  # missing a counts column
  with pytest.raises(InvalidDesignException) :
    mat = CountMatrix(
      fake_counts_pandas_dataframe
      ,column_data=fake_column_data_pandas_dataframe
      ,design='cont_cov ~ category[case]'
    )
  

  # set invalid design
  with pytest.raises(InvalidDesignException) :
    mat = CountMatrix(
      fake_counts_pandas_dataframe
      ,column_data=fake_column_data_pandas_dataframe
      ,design='cont_cov ~ category[case] + counts'
    )
    mat.design = 'oogabooga'
   
  # with strict
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,column_data=fake_column_data_pandas_dataframe
    ,strict=True
  )
  assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
  assert all(mat.feature_names == fake_counts_pandas_dataframe.index)

  # with violations of strict
  # change the order of count columns wrt column data
  fake_counts_pandas_dataframe.columns = fake_counts_pandas_dataframe.columns[::-1]
  with pytest.raises(SampleMismatchException) :
    mat = CountMatrix(
      fake_counts_pandas_dataframe
      ,column_data=fake_column_data_pandas_dataframe
      ,strict=True
    )

  # add an additional column
  fake_counts_pandas_dataframe['d'] = 0
  with pytest.raises(SampleMismatchException) :
    mat = CountMatrix(
      fake_counts_pandas_dataframe
      ,column_data=fake_column_data_pandas_dataframe
      ,strict=True
    )
  
  # with different sample names and not strict
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,column_data=fake_column_data_pandas_dataframe
    ,strict=False
  )
  assert sorted(mat.sample_names) == sorted(fake_column_data_pandas_dataframe.index)

  # bad cov
  with pytest.raises(InvalidDesignException) :
    mat.design = 'category ~ cont_covx + counts'

def test_CountMatrixFile(
  fake_counts_csv
  ,fake_column_data_csv
  ) :
  from de_toolkit import CountMatrixFile

  mat = CountMatrixFile(
    fake_counts_csv
    ,column_data_f=fake_column_data_csv
  )
