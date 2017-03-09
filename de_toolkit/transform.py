'''
Usage:
  detk-transform vst <counts_fn> <cov_fn>
  detk-transform ruvseq <counts_fn>
  detk-transform trim <counts_fn>
  detk-transform shrink <counts_fn>
'''
from docopt import docopt
from .util import (
  count_obj_to_DESeq2
  ,load_count_mat_file
  ,require_rpy2
  ,require_deseq2
  ,rpy2_console_wrapper
  ,stub
)

def pmf_transform(x,shrink_factor=0.25,max_p=None,iters=1000) :

  x = x.copy()
  max_p = max_p or sqrt(1./len(x))

  for i in range(iters) :
    p_x = x/x.sum()

    if x.sum() == 0 :
      print('all samples set to zero, returning')
      break

    p_x_outliers = p_x>max_p

    if not any(p_x_outliers) :
      break # done

    max_non_outliers = max(x[~p_x_outliers])

    x[p_x_outliers] = max_non_outliers+(x[p_x_outliers]-max_non_outliers)*shrink_factor

  if i == iters :
    print('PMF transform did not converge')
    print(p_x)
    print(p_x_outliers)

  return x

@stub
def shrink_outliers(count_obj) :
  pass

@stub
def trim_outliers(count_obj) :
  pass

@require_deseq2
def vst(count_obj) :
  from rpy2 import robjects
  from rpy2.rinterface import RRuntimeError
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr
  import warnings

  base = importr('base')

  # TODO: consider wrapping this in a try except
  deseq = importr('DESeq2')
  sumexp = importr('SummarizedExperiment')

  dds = count_obj_to_DESeq2(count_obj)

  with rpy2_console_wrapper() as rpy2_f :
    try :
      vsd = deseq.varianceStabilizingTransformation(dds)
      vsd_values = sumexp.assay(vsd)
    except RRuntimeError as e :
      print(e)
      raise
    print(rpy2_f.getvalue())

  return vsd_values

@stub
def ruvseq(count_obj) :
  pass

def main(argv=None) :

  args = docopt(__doc__,argv=argv)

  count_obj = load_count_mat_file(args['<counts_fn>'])

  if args['<cov_fn>'] is not None :
    count_obj.add_column_data(args['<cov_fn>'])

  if args['vst'] :
    count_obj.transform(vst)

  elif args['ruvseq'] :
    ruvseq(count_obj)
  elif args['trim'] :
    trim_outliers(count_obj)
  elif args['shrink'] :
    shrink_outliers(count_obj)

if __name__ == '__main__' :
  main()
