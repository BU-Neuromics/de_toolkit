import pytest
from de_toolkit.wrapr import check_r, check_deseq2

# decorator for skipping if rpy2 is not installed
r_test = pytest.mark.skipif(not check_r(),reason='r is not installed, skipping test')
deseq2_test = pytest.mark.skipif(not check_deseq2(),reason='rpy2 not installed, skipping test')

@r_test
def test_require_deseq2(monkeypatch) :
  from de_toolkit import wrapr
  from de_toolkit.wrapr import RPackageMissingError, require_deseq2
  def f(*args,**kwargs):
    return wrapr('TRUE')
  mokneypatch.setattr(wrapr,'wrapr',f)

  with pytest.raises(RPackageMissingError) :
    require_deseq2(lambda x: x)

@deseq2_test
def old_test_count_obj_to_DESeq2(fake_counts_obj) :
  from de_toolkit.util import count_obj_to_DESeq2
  from rpy2.robjects import r
  from rpy2.robjects.packages import importr
  import warnings

  base = importr('base')
  deseq2 = importr('DESeq2')

  # the design associated with fake_counts_obj is category ~ counts
  # which is intended for testing Firth
  # change it to something DESeq2 expects

  fake_counts_obj.design = 'counts ~ cont_cov + category'

  # this raises R warnings about converting floats to integers that we can
  # ignore
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dds = count_obj_to_DESeq2(fake_counts_obj)

  r_counts = deseq2.counts_DESeqDataSet(dds)
  check_numpy_r_matrix_equal(r_counts,fake_counts_obj.counts.as_matrix())

  robj = r['as.data.frame'](dds.slots['colData'])
  check_pandas_r_dataframes_equal(robj,fake_counts_obj.design_matrix.full_matrix)

  # just make sure the normalization we get back is correct
  #from de_toolkit.norm import deseq2 as deseq2_norm
  #py_norm_counts = deseq2_norm(fake_counts_obj)
  #r_norm_counts = deseq2.counts_DESeqDataSet(dds,normalized=True)
  #check_numpy_r_matrix_equal(r_norm_counts,py_norm_counts.as_matrix())
