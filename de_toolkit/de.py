'''
Usage:
  detk-de deseq2 <model> <count_fn> <cov_fn>
  detk-de firth
  detk-de t-test
'''
from docopt import docopt
from .util import require_rpy2, stub

@require_rpy2
def deseq2(count_obj) :
  import rpy2
  pass

@stub
@require_rpy2
def firth_logistic_regression(count_obj) :
  pass

@stub
def t_test(count_obj) :
  pass

def main() :

  args = docopt(__doc__)

  count_obj = load_count_mat_file(args['<count_fn>'])

  if '<model>' in args :
    count_obj.add_model(args['<model>'])

  if '<cov_fn>' in args :
    count_obj.add_covariates(args['<cov_fn>'])

  if args['deseq2'] :
    deseq2(count_obj)
  elif args['firth'] :
    firth_logistic_regression('and junk')

