'''
Usage:
  detk-transform vst <counts_fn>
  detk-transform ruvseq <counts_fn>
  detk-transform trim <counts_fn>
  detk-transform shrink <counts_fn>
'''
from docopt import docopt
from .util import stub, load_count_mat_file, require_rpy2

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
def shrink_outliers(count_mat) :
  pass

@stub
def trim_outliers(count_mat) :
  pass

@require_rpy2
def vst(count_mat) :
  pass

@stub
def ruvseq(count_mat) :
  pass

def main(argv=None) :

  args = docopt(__doc__,argv=argv)

  count_obj = load_count_mat_file(args['<counts_fn>'])

  if '<cov_fn>' in args :
    count_obj.add_covariates(args['<cov_fn>'])

  if args['vst'] :
    vst(count_obj)
  elif args['ruvseq'] :
    ruvseq(count_obj)
  elif args['trim'] :
    trim_outliers(count_obj)
  elif args['shrink'] :
    shrink_outliers(count_obj)

if __name__ == '__main__' :
  main()
