'''
Usage:
  detk-de deseq2 <design> <count_fn> <cov_fn>
  detk-de firth <design> <count_fn> <cov_fn>
  detk-de t-test <count_fn> <cov_fn>
'''
from docopt import docopt
from .util import (
  column_data_rtype_dict
  ,column_data_to_r_dataframe
  ,count_obj_to_r_matrix
  ,load_count_mat_file
  ,require_rpy2
  ,stub
)

@require_rpy2
def deseq2(count_obj) :
  import rpy2
  pass

@require_rpy2
def firth_logistic_regression(count_obj) :

  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr
  from rpy2.rinterface import RRuntimeError

  base = importr('base')

  try :
    logistf = importr('logistf')
  except RRuntimeError as e :
    raise Exception('logistf must be installed to use this function')

  # create a dataframe of the column_data, if there are any
  if count_obj.column_data is None :
    raise Exception('DESeq2 requires colData, add column '
      'dataframe to count object'
    )

  colData_rtype_dict = column_data_rtype_dict(count_obj)

  # by default, the design is assumed the be in the first non-sample name column
  # of column_data
  design = '{} ~'.format(count_obj.column_data.columns[0])
  if count_obj.design is not None :
    design = count_obj.design
  if not design.strip().endswith('~') :
    design += ' + '
  design += ' counts'

  # logistf can hang when the dependent variable isn't an integer vector
  endog = design.split('~')[0].strip()
  endog_levels = sorted(list(set(colData_rtype_dict[endog])))
  endog_vals = []
  for level in colData_rtype_dict[endog] :
    endog_vals.append(endog_levels.index(level))
  colData_rtype_dict[endog] = robjects.IntVector(endog_vals)
  design_formula = robjects.Formula(design)

  fits = []
  for i in range(count_obj.counts.shape[0]) :
    gene_counts = count_obj.counts.ix[i]
    colData_rtype_dict['counts'] = robjects.FloatVector(gene_counts)

    od = rlc.OrdDict(list(colData_rtype_dict.items()))
    data = robjects.DataFrame(od)
    fit = logistf.logistf(design_formula,data=data)
    fits.append(fit)

  print(fits)

@stub
def t_test(count_obj) :
  pass

def main(argv=None) :

  args = docopt(__doc__,argv=argv)

  count_obj = load_count_mat_file(args['<count_fn>'])

  count_obj.add_design(args['<design>'])

  count_obj.add_column_data(args['<cov_fn>'])

  if args['deseq2'] :
    count_obj.add_design(args['<design>'])
    deseq2(count_obj)
  elif args['firth'] :
    count_obj.add_design(args['<design>'])
    firth_logistic_regression(count_obj)

if __name__ == '__main__' :
  main()
