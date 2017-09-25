from .common import CountMatrixFile
from .patsy_lite import ModelError
from contextlib import contextmanager

################################################################################
# all the rpy2 stuffs
def check_rpy2() :
  try :
    import rpy2
    return True
  except ImportError as e :
    return False

class Rpy2ImportError(ImportError) : pass
class RPackageMissingError(Exception) : pass

def check_rpy2_or_raise() :
  if not check_rpy2() :
    raise Rpy2ImportError('rpy2 must be installed to use this function')

def require_rpy2(f) :
  check_rpy2_or_raise()
  return f

class Stub(Exception): pass
def stub(f) :
  def stub(*args,**kwargs) :
    raise Stub('Not yet implemented - {}.{}'.format(f.__module__,f.__name__))
  return stub

@require_rpy2
def check_deseq2() :
  from rpy2.rinterface import RRuntimeError
  try :
    from rpy2.robjects.packages import importr
    deseq = importr('DESeq2')
    return True
  except RRuntimeError as e :
    return False

def check_deseq2_or_raise():
  if not check_deseq2() :
    raise RPackageMissingError('DESeq2 must be installed to use this function')
  return True

def require_deseq2(f) :
  check_deseq2_or_raise()
  return f

@require_rpy2
def pandas_dataframe_to_r_matrix(df) :

  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr

  base = importr('base')

  # create a numerical matrix of counts
  nrow, ncol = df.shape
  rmat = base.matrix(
    robjects.FloatVector(df.unstack())
    ,nrow=nrow
    ,ncol=ncol
  )
  rmat.rownames = robjects.StrVector(df.index.tolist())
  rmat.colnames = robjects.StrVector(df.columns.tolist())

  return rmat

class RDatatypeException(Exception): pass
@require_rpy2
def pandas_dataframe_to_r_dataframe(df) :
  '''return dictionary form of pandas dataframe *df* with values as vectors of
  the appropriate R datatype (e.g. FloatVector)

  Convert the pandas dataframe to an :py:`collections.OrderedDict` of R vectors
  of the appropriate type according to the column Series dtype. Mapping is:

  +-------------+---------------+
  | numpy.dtype | robjects type |
  +-------------+---------------+
  |   float64   |  FloatVector  |
  |    int64    |   IntVector   |
  |    bool     |  BoolVector   |
  |  O (object) |   StrVector   |
  +-------------+---------------+

  Unrecognized dtypes will raise an RDatatypeException.

  :param df: pandas DataFrame object
  :returns: :py:`collections.OrderedDict` of R vectors of the appropriate type
  :rtype:  :py:`collections.OrderedDict`
  '''

  from collections import OrderedDict
  import numpy
  from rpy2.robjects.vectors import DataFrame, BoolVector, FloatVector, IntVector, StrVector
  from rpy2.robjects.packages import importr
  import rpy2.rlike.container as rlc

  base = importr('base')

  def error(x) :
    dtype = x.dtype
    raise RDatatypeException(('Unrecognized dtype in dataframe ({}), cannot convert '
        'to r dataframe').format(dtype))
  dtype_to_rtype_map = {
    numpy.dtype('float64'): FloatVector
    ,numpy.dtype('int64'): IntVector
    ,numpy.dtype('bool'): BoolVector
    # base.I prevents the StrVector from being converted to a FactorVector by R
    ,numpy.dtype('O'): lambda x: base.I(StrVector(x))
  }

  d = OrderedDict()

  for k,v in df.iteritems() :
    rtype = dtype_to_rtype_map.get(v.dtype,error)
    d[k] = rtype(v)

  r_df = DataFrame(d)
  r_df.rownames = base.I(StrVector(df.index.tolist()))

  return r_df

@require_deseq2
def count_obj_to_DESeq2(count_obj) :
  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr

  base = importr('base')

  deseq = importr('DESeq2')

  countData = pandas_dataframe_to_r_matrix(count_obj.counts)

  # if count_obj has no column data, make some up so DESeq2
  # doesn't whine
  if count_obj.column_data is None :
    colData = pandas.DataFrame([
      pandas.Series([1]*count_obj.counts.shape[1]
              ,name='dummy')]
      ,index=count_obj.columns
    )
  else :
    colData = count_obj.column_data

  # if the count_obj doesn't have a model, provide the trivial
  # model
  if count_obj.design is None :
    design = '~ 1'
  else :
    # remove intercept
    count_obj.design_matrix.drop_from_rhs('Intercept',quiet=True)
    design = count_obj.design
    colData = count_obj.design_matrix.full_matrix

  # create the dataset object
  dds = deseq.DESeqDataSetFromMatrix(
    countData=countData
    ,colData=pandas_dataframe_to_r_dataframe(colData)
    ,design=robjects.Formula(design)
  )

  return dds

@require_rpy2
@contextmanager
def rpy2_console_wrapper() :
  import io
  import rpy2

  old_writeconsole_regular = rpy2.rinterface.get_writeconsole_regular()
  old_writeconsole_warnerror = rpy2.rinterface.get_writeconsole_warnerror()

  f = io.StringIO()

  def write_console(s) :
    f.write(s)
    f.flush()

  rpy2.rinterface.set_writeconsole_regular(write_console)
  rpy2.rinterface.set_writeconsole_warnerror(write_console)

  yield f

  f.close()

  rpy2.rinterface.set_writeconsole_regular(old_writeconsole_regular)
  rpy2.rinterface.set_writeconsole_warnerror(old_writeconsole_warnerror)

################################################################################
