'''
Usage:
  detk-de deseq2 [options] [--rda=RDA] <design> <count_fn> <cov_fn>
  detk-de firth [options] [--rda=RDA] <design> <count_fn> <cov_fn>
  detk-de t-test <count_fn> <cov_fn>

Options:
  -o FILE --output=FILE    Destination of primary output [default: stdout]
  --rda=RDA                Filename passed to saveRDS() R function of the result
                           objects from the analysis
  --strict    Require that the sample order indicated by the column names in the
              counts file are the same as, and in the same order as, the
              sample order in the row names of the covariates file

'''
from docopt import docopt
import pandas
import sys
from .common import CountMatrixFile
from .util import (
  column_data_rtype_dict
  ,column_data_to_r_dataframe
  ,count_obj_to_r_matrix
  ,load_count_mat_file
  ,require_rpy2
  ,require_deseq2
  ,stub
)

@require_deseq2
def deseq2(count_obj) :
  import rpy2
  pass

@require_rpy2
def firth_logistic_regression(count_obj,rda=None) :

  count_obj.check_model() # make sure the model is valid

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
    raise Exception('Firth requires colData, add column '
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

  # fits stores a list of tuples of the form (rfit,'status')
  # the status records info from firth about the specific gene
  # currently it only stores whether the profile likelihood or Wald
  # method was used to calculate confidence intervals
  fits = []
  for i in range(count_obj.counts.shape[0]) :
    gene_counts = count_obj.counts.iloc[i]
    colData_rtype_dict['counts'] = robjects.FloatVector(gene_counts)

    od = rlc.OrdDict(list(colData_rtype_dict.items()))
    data = robjects.DataFrame(od)

    # issue #3 is caused by the Firth profile likelihood based confidence
    # interval method producing incoherent results on certain data (can't
    # figure out what exactly)
    # attempt the regression with profile likelihood on by default and if
    # it crashes fall back on the Wald method and move on
    try :
      fit = (
        logistf.logistf(design_formula,data=data,pl=True)
        ,'PL'
      )
    except RRuntimeError as exc :
      # capture this exact error, otherwise raise
      if 'NA/NaN/Inf in foreign function call (arg 10)' in str(exc) :
        fit = (
          logistf.logistf(design_formula,data=data,pl=False)
          ,'Wald'
        )
      else :
        raise

    fits.append(fit)

  # members of fit list
  # "coefficients"      "alpha"      "terms"      "var"
  # "formula"           "call"       "conv"       "firth"
  # "method.ci"         "ci.lower"   "ci.upper"   "conflev"
  # "df"                "loglik"     "iter"       "n"       "y"
  # "linear.predictors" "predict"    "hat.diag"   "method"  "prob"
  # "pl.iter"           "betahist"   "pl.conv"    "data"    "weights"

  fields = ('beta','p','padj'
    #,'ci.upper','ci.lower','loglik'
  )

  # these are the model variables
  var_names = list(fits[0][0].rx2('terms'))

  int_i = var_names.index('(Intercept)')
  var_names[int_i] = 'int'
  var_names = [_.replace(' ','_') for _ in var_names]

  colnames = ['{}__{}'.format(_i,_j) for _i in var_names for _j in fields]

  firth_props = pandas.DataFrame([]
   ,index=count_obj.counts.index.tolist()
   ,columns=colnames+['status']
  )

  for i,row in enumerate(firth_props.index) :

    fit,status = fits[i]

    # coefficients
    cols = ['{}__beta'.format(_) for _ in var_names]
    firth_props.loc[row,cols] = fit.rx2('coefficients')

    # p-values
    cols = ['{}__p'.format(_) for _ in var_names]
    firth_props.loc[row,cols] = fit.rx2('prob')

    # ci.upper
    #cols = ['{}__ci.upper'.format(_) for _ in var_names]
    #firth_props.loc[row,cols] = fit.rx2('ci.upper')

    # ci.lower
    #cols = ['{}__ci.lower'.format(_) for _ in var_names]
    #firth_props.loc[row,cols] = fit.rx2('ci.lower')

    # loglik
    #cols = ['{}__loglik'.format(_) for _ in var_names]
    #firth_props.loc[row,cols] = fit.rx2('loglik')

    # status
    firth_props.loc[row,'status'] = status

  stats = importr('stats')

  for var in var_names :
    p_adjust = stats.p_adjust(
      robjects.FloatVector(firth_props['{}__p'.format(var)])
      ,method = 'BH'
    )
    firth_props['{}__padj'.format(var)] = p_adjust

  if rda is not None :
    robjects.r['saveRDS'](fits,rda)

  return firth_props

@stub
def t_test(count_obj) :
  pass

def main(argv=None) :

  args = docopt(__doc__,argv=argv)

  #count_obj = load_count_mat_file(args['<count_fn>'])
  count_obj = CountMatrixFile(
    args['<count_fn>']
    ,args['<cov_fn>']
    ,design=args['<design>']
    ,strict=args.get('--strict',False)
  )

  if args['deseq2'] :
    count_obj.add_design(args['<design>'])
    deseq2(count_obj)
  elif args['firth'] :
    count_obj.add_design(args['<design>'])
    firth_out = firth_logistic_regression(count_obj,rda=args['--rda'])

    if args['--output'] == 'stdout' :
      f = sys.stdout
    else :
      f = args['--output']

    firth_out.to_csv(f,sep='\t')

if __name__ == '__main__' :

  main()
