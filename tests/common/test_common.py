import docopt
import pytest
from de_toolkit.common import main

def test_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_patsy_lite() :
  from de_toolkit.common import patsy_lite

  assert patsy_lite('var') == 'var'
  assert patsy_lite('var[lev]') == 'C(var, Treatment("lev"))'
  assert patsy_lite('var[lev] ~ 1') == 'C(var, Treatment("lev")) ~ 1'
  assert patsy_lite('1 ~ var[lev]') == '1 ~ C(var, Treatment("lev"))'
  assert patsy_lite('var[lev1,lev2]') == 'C(var, levels=["lev1","lev2"])'

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

  # with explicit sample and count names
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,sample_names=fake_counts_pandas_dataframe.columns
    ,count_names=fake_counts_pandas_dataframe.index
  )
  assert all(mat.sample_names == fake_counts_pandas_dataframe.columns)
  assert all(mat.count_names == fake_counts_pandas_dataframe.index)

  # with no explicit index or names
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,column_data=fake_column_data_pandas_dataframe
  )
  assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
  assert all(mat.count_names == fake_counts_pandas_dataframe.index)

  # with strict
  mat = CountMatrix(
    fake_counts_pandas_dataframe
    ,column_data=fake_column_data_pandas_dataframe
    ,strict=True
  )
  assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
  assert all(mat.count_names == fake_counts_pandas_dataframe.index)

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

def test_CountMatrixFile(
  fake_counts_csv
  ,fake_column_data_csv
  ) :
  from de_toolkit import CountMatrixFile

  mat = CountMatrixFile(
    fake_counts_csv
    ,column_data_f=fake_column_data_csv
  )
