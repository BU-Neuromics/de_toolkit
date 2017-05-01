'''
Usage:
  detk norm [<args>...]
  detk de [<args>...]
  detk transform [<args>...]
  detk filter [<args>...]
  detk stats [<args>...]
  detk help [<args>...]

Options:

'''
from docopt import docopt
import pandas

class InvalidDesignException(Exception): pass
class SampleMismatchException(Exception): pass

class CountMatrix(object) :
  def __init__(self
      ,counts
      ,count_names=None
      ,sample_names=None
      ,column_data=None
      ,design=None
      ,strict=False
     ) :
    self.column_data = column_data
    self.design = design

    self.counts = counts
    if count_names is not None :
      self.counts.index = count_names
    if sample_names is not None :
      self.counts.columns = sample_names

    self.sample_names = self.counts.columns
    self.count_names = self.counts.index

    if self.column_data is not None :
      # line up the sample names from the column_data and counts matrices
      if strict and (
        len(self.column_data.index) != len(self.counts.columns) or
        not all(self.column_data.index == self.counts.columns)
      ) :
        raise SampleMismatchException('When *strict* is supplied, the columns '
          'of the counts file must correspond exactly to the row names in the '
          'column_data matrix')
      else :
        common_names = self.sample_names.intersection(self.column_data.index)

        # fix to "no memory available" bitbucket issue #4 when matrices are
        # empty
        if len(common_names) < 2 :
          raise SampleMismatchException('No sample names were found to be in '
            'common between the counts and column data or specified sample '
            'names. Check that the first column of the column_data matrix '
            'contains at least 2 values in common')

        self.sample_names = common_names
        self.counts = self.counts[common_names]
        self.column_data = self.column_data.loc[common_names]

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

class CountMatrixFile(CountMatrix) :

  def __init__(self
    ,count_f
    ,column_data_f=None
    ,design=None
    ,**kwargs
   ) :

    counts = pandas.read_csv(
      count_f
      ,sep=None # sniff the format automatically
      ,engine='python'
      ,index_col=0
    )

    column_data = None
    if column_data_f is not None :
      column_data = pandas.read_csv(
        column_data_f
        ,sep=None
        ,engine='python'
        ,index_col=0
      )

    CountMatrix.__init__(self
      ,counts
      ,column_data=column_data
      ,design=design
      ,**kwargs
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
