'''
Usage:
  detk norm [<args>...]
  detk de [<args>...]
  detk transform [<args>...]
  detk filter [<args>...]
  detk stats [<args>...]
  detk help [<args>...]
'''
from docopt import docopt
import pandas

class CountMatrix(object) :
  def __init__(self,count_f) :
    self.model = None
    self.covariates = None

    self.counts = pandas.read_csv(
      count_f
      ,sep=None # sniff the format automatically
      ,engine='python'
      ,index_col=0
    )

    self.sample_names = self.counts.columns
    self.count_names = self.counts.index

  def add_covariates(self,cov_f) :
    self.covariates = pandas.read_csv(
      cov_f
      ,sep=None
    )

  def normalized(self,method='deseq2') :
    pass

def main() :
  
  args = docopt(__doc__)

  if args['norm'] :
    from .norm import main
    main()
  elif args['de'] :
    from .de import main
    main()
  elif args['transform'] :
    from .transform import main
    main()
  elif args['filter'] :
    from .filter import main
    main()
  elif args['stats'] :
    from .stats import main
    main()
  elif args['help'] :
    docopt(__doc__,['-h'])
