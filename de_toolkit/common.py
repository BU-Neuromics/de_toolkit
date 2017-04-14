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

class InvalidDesignException(Exception): pass

class CountMatrixFile(CountMatrix) :

  def __init__(self,count_f) :

    counts = pandas.read_csv(
      count_f
      ,sep=None # sniff the format automatically
      ,engine='python'
      ,index_col=0
    )

    CountMatrix.__init__(self,counts,counts.index,counts.columns)


class CountMatrix(object) :
  def __init__(self,counts,index=None,columns=None) :
    self.design = None
    self.column_data = None

    self.counts = counts
    if index :
      self.counts.index = index
    if columns :
      self.counts.columns = columns

    self.sample_names = self.counts.columns
    self.count_names = self.counts.index

    # members to keep track of count mutations
    self.transformed = {}
    self.normalized = {}

  def add_column_data(self,cov_f) :
    self.column_data = pandas.read_csv(
      cov_f
      ,sep=None
      ,engine='python'
      ,index_col=0
    )

  def add_design(self,design) :
    self.design = design

  def transform(self,transf) :
    self.transformed[transf.__name__] = transf(self)

  def add_normalized(self,method='deseq2') :
    pass

  def check_model(self) :
    '''Make sure the design variables match the column data.
    Raise InvalidDesignException if variables specified in the design
    do not appear in the column data.
    '''

    if self.design is not None :
      if self.column_data is None :
        raise InvalidDesignException(
          'Design specified but no column data provided. Both must be '
          'added to CountMatrix object to use a design.'
        )
      vars = self.design.split(' ')
      vars = [_.strip() for _ in vars if _.strip() not in ('~','')]

      for var in vars :
        if var not in self.column_data.columns :
          raise InvalidDesignException((
            'Variable {} not found in column data columns {}. Check formula '
            'and/or column data columns.').format(var,self.column_data.columns)
          )
def main(argv=None) :
  
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

if __name__ == '__main__' :
  main()
