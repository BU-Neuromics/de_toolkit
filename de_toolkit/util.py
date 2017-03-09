from .common import CountMatrix
from contextlib import contextmanager

def load_count_mat_file(count_fn) :
  with open(count_fn) as f :
    count_obj = CountMatrix(f)
  return count_obj

def require_rpy2(f) :
  try :
    import rpy2
  except ImportError as e :
    raise Exception('rpy2 must be installed to use this function')
  return f

class Stub(Exception): pass
def stub(f) :
  def stub(*args,**kwargs) :
    raise Stub('Not yet implemented - {}.{}'.format(f.__module__,f.__name__))
  return stub

@require_rpy2
def require_deseq2(f) :
  try :
    from rpy2.robjects.packages import importr
    deseq = importr('DESeq2')
  except ImportError as e :
    raise Exception('DESeq2 must be installed to use this function')
  return f

@require_deseq2
def count_obj_to_DESeq2(count_obj) :
  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr

  base = importr('base')

  # TODO: consider wrapping this in a try except
  deseq = importr('DESeq2')

  # create a numerical matrix of counts
  nrow, ncol = count_obj.counts.shape
  counts = base.matrix(
    robjects.IntVector(count_obj.counts.unstack())
    ,nrow=nrow
    ,ncol=ncol
  )
  counts.rownames = robjects.StrVector(count_obj.counts.index.tolist())
  counts.colnames = robjects.StrVector(count_obj.counts.columns.tolist())

  # create a dataframe of the column_data, if there are any
  countData = counts
  if count_obj.column_data is None :
    raise Exception('DESeq2 requires colData, add column dataframe to count object')

  # TODO: figure out how to pick the correct robject function
  # based on pandas column dtype
  col_data_kv = [(k,robjects.StrVector(v.tolist())) for k,v in count_obj.column_data.iteritems()]
  od = rlc.OrdDict(col_data_kv)

  colData = robjects.DataFrame(od)
  colData.rownames = robjects.StrVector(count_obj.column_data.index.tolist())

  # by default, the design is assumed the be in the first non-sample name column
  # of column_data
  design = '~ {}'.format(count_obj.column_data.columns[0])
  if count_obj.design is not None :
    design = count_obj.design
  design = robjects.Formula(design)

  # create the dataset object
  dds = deseq.DESeqDataSetFromMatrix(
    countData=countData
    ,colData=colData
    ,design=design
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

