import pytest
from de_toolkit.util import check_rpy2, check_deseq2

# decorator for skipping if rpy2 is not installed
rpy2_test = pytest.mark.skipif(not check_rpy2(),reason='rpy2 not installed, skipping test')
deseq2_test = pytest.mark.skipif(not check_deseq2(),reason='rpy2 not installed, skipping test')

@rpy2_test
def test_require_deseq2(monkeypatch) :
  from rpy2.rinterface import RRuntimeError
  import rpy2.robjects.packages as rrp
  from de_toolkit.util import RPackageMissingError, require_deseq2
  def f(*args,**kwargs):
    raise(RRuntimeError('mock'))
  monkeypatch.setattr(rrp,'importr',f)

  with pytest.raises(RPackageMissingError) :
    require_deseq2(lambda x: x)

def check_pandas_robj_dimnames_equal(robj, df) :
  assert all([_[0]==_[1] for _ in zip(robj.colnames,df.columns)])
  assert all([_[0]==_[1] for _ in zip(robj.rownames,df.index)])

def check_numpy_r_matrix_equal(robj, mat) :
  import numpy
  assert numpy.allclose(numpy.asarray(robj),mat)

@rpy2_test
def test_pandas_dataframe_to_r_matrix(fake_counts_obj) :
  from de_toolkit.util import pandas_dataframe_to_r_matrix
  df = fake_counts_obj.counts
  robj = pandas_dataframe_to_r_matrix(df)
  check_numpy_r_matrix_equal(robj,df.as_matrix())
  check_pandas_robj_dimnames_equal(robj,df)

def check_pandas_r_dataframes_equal(robj,df) :
  import numpy
  from rpy2.robjects import r
  check_pandas_robj_dimnames_equal(robj,df)
  for i, (col, val) in enumerate(df.items()) :
    r_val = robj.rx2(i+1)
    for r_i, p_i in zip(r_val,val) :
      assert r_i == p_i

@rpy2_test
def test_pandas_dataframe_to_r_dataframe(fake_counts_obj) :

  import pandas
  from rpy2 import robjects
  from de_toolkit.util import pandas_dataframe_to_r_dataframe, RDatatypeException

  # robj is an OrdDict object from rpy2.rlike.container
  # behaves like a python dictionary

  # test counts
  df = fake_counts_obj.counts
  robj = pandas_dataframe_to_r_dataframe(df)
  check_pandas_r_dataframes_equal(robj,df)

  # and column data 
  df = fake_counts_obj.column_data
  # there aren't any bools in the column_data fixture, add a col
  df['test_bool'] = True
  robj = pandas_dataframe_to_r_dataframe(df)
  check_pandas_r_dataframes_equal(robj,df)

  # datetime dtypes are not understood by R, make sure it raises
  df['datetime'] = pandas.Timestamp('19700101')
  with pytest.raises(RDatatypeException) :
    pandas_dataframe_to_r_dataframe(df)

@deseq2_test
def test_count_obj_to_DESeq2(fake_counts_obj) :
  from de_toolkit.util import count_obj_to_DESeq2
  from rpy2.robjects import r
  from rpy2.robjects.packages import importr
  import warnings

  base = importr('base')
  deseq2 = importr('DESeq2')

  # the design associated with fake_counts_obj is category ~ counts
  # which is intended for testing Firth
  # change it to something DESeq2 expects

  fake_counts_obj.design = '~ cont_cov + category'

  # this raises R warnings about converting floats to integers that we can
  # ignore
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dds = count_obj_to_DESeq2(fake_counts_obj)

  r_counts = deseq2.counts_DESeqDataSet(dds)
  check_numpy_r_matrix_equal(r_counts,fake_counts_obj.counts.as_matrix())

  robj = r['as.data.frame'](dds.slots['colData'])
  check_pandas_r_dataframes_equal(robj,fake_counts_obj.column_data)

  # just make sure the normalization we get back is correct
  #from de_toolkit.norm import deseq2 as deseq2_norm
  #py_norm_counts = deseq2_norm(fake_counts_obj)
  #r_norm_counts = deseq2.counts_DESeqDataSet(dds,normalized=True)
  #check_numpy_r_matrix_equal(r_norm_counts,py_norm_counts.as_matrix())
