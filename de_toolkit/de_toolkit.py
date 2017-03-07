from .norm import deseq2, trimmed_mean, reference, custom_norm
from .util import load_count_mat_file

class CountMatrix(object) :
  def __init__(self,count_f) :
    model = None
    covariates = None
    pass

  def add_covariates(self,cov_f) :
    pass

  def normalized(self,method='deseq2') :
    pass
