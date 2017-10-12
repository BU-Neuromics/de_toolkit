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
from .common import CountMatrixFile, InvalidDesignException
from .util import (
  pandas_dataframe_to_r_dataframe
  ,pandas_dataframe_to_r_matrix
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

  # make a copy of count_obj, since we mutate it
  count_obj = count_obj.copy()

  # validate the design matrix
  if count_obj.design is None or count_obj.design_matrix is None :
    raise InvalidDesignException('count_obj must have a design matrix in Firth'
      ' logistic regression')

  if 'counts' not in count_obj.design_matrix.rhs :
    raise InvalidDesignException('The term "counts" must exist on the right hand'
      'side of the model in Firth logistic regression')

  # make sure the rhs of the design matrix doesn't have an intercept
  count_obj.design_matrix.drop_from_rhs('Intercept',quiet=True)

  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr
  from rpy2.rinterface import RRuntimeError

  base = importr('base')

  try :
    logistf = importr('logistf')
  except RRuntimeError as e :
    raise Exception('logistf must be installed to use this function')

  design_formula = robjects.Formula(count_obj.design)

  # fits stores a list of tuples of the form (rfit,'status')
  # the status records info from firth about the specific gene
  # currently it only stores whether the profile likelihood or Wald
  # method was used to calculate confidence intervals
  fits = []
  for i in range(count_obj.counts.shape[0]) :
    gene_counts = count_obj.counts.iloc[i]
    #colData_rtype_dict['counts'] = robjects.FloatVector(gene_counts)

    count_obj.design_matrix.update_design('counts',gene_counts)

    # the R object we will pass to 
    full_matrix_robj = pandas_dataframe_to_r_dataframe(
      count_obj.design_matrix.full_matrix
    )

    # issue #3 is caused by the Firth profile likelihood based confidence
    # interval method producing incoherent results on certain data (can't
    # figure out what exactly)
    # attempt the regression with profile likelihood on by default and if
    # it crashes fall back on the Wald method and move on
    try :
      fit = (
        logistf.logistf(design_formula,data=full_matrix_robj,pl=True)
        ,'PL'
      )
    except RRuntimeError as exc :
      # capture this exact error, otherwise raise
      if 'NA/NaN/Inf in foreign function call (arg 10)' in str(exc) :
        fit = (
          logistf.logistf(design_formula,data=full_matrix_robj,pl=False)
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

  firth_props = pandas.DataFrame(
   index=count_obj.counts.index.tolist()
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

  # cast all columns to numeric if possible
  firth_props = firth_props.apply(pandas.to_numeric,errors='ignore')

  return firth_props

@stub
def t_test(count_obj) :
  pass

def main(argv=None) :

  args = docopt(__doc__,argv=argv)

  count_obj = CountMatrixFile(
    args['<count_fn>']
    ,args['<cov_fn>']
    ,design=args['<design>']
    ,strict=args.get('--strict',False)
  )

  if args['deseq2'] :
    deseq2(count_obj)
  elif args['firth'] :
    firth_out = firth_logistic_regression(count_obj,rda=args['--rda'])

    if args['--output'] == 'stdout' :
      f = sys.stdout
    else :
      f = args['--output']

    firth_out.to_csv(f,sep='\t')

if __name__ == '__main__' :

  main()
