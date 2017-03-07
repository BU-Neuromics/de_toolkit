'''
Usage:
  detk-norm [<args>...]
  detk-de [<args>...]
  detk-transform [<args>...]
  detk-filter [<args>...]
  detk-stats [<args>...]
  detk help [<args>...]
'''
from docopt import docopt
import de_toolkit.norm as norm
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

def main() :
  
  args = docopt(__doc__)

  if args['norm'] :
    norm.main()
