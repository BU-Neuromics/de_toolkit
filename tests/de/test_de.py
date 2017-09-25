
import docopt
from itertools import cycle
import numpy
import pandas
import pytest
from de_toolkit.common import CountMatrix
from de_toolkit.de import main
import warnings

def test_de_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_firth_cli(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ counts',fake_counts_csv,fake_column_data_csv])

def test_firth_cli_w_cov(fake_counts_csv,fake_column_data_csv) :
  main(['firth','category ~ cont_cov + counts',fake_counts_csv,fake_column_data_csv])

@pytest.fixture
def logistic_test_counts_obj() :
  N = 5000
  N1 = int(N/2)
  N2 = N-N1
  counts = pandas.DataFrame(
    columns=['gene{}'.format(_) for _ in range(N)]
    ,index=('gene1','gene2','gene3')
    ,dtype='float64'
  )
  # null
  counts.loc['gene1'] = numpy.random.randint(100,size=N)
  # up in case
  counts.loc['gene2'] = numpy.concatenate([
    numpy.random.normal(0.75,1,size=N1)
    ,numpy.random.normal(0.25,1,size=N2)
  ])
  # up in control
  counts.loc['gene3'] = numpy.concatenate([
    numpy.random.normal(0.25,1,size=N1)
    ,numpy.random.normal(0.75,1,size=N2)
  ])

  cov_cycle = cycle(['high','low'])
  column_data = pandas.DataFrame({
      'category': ['case']*(N1)+['control']*(N2)
      ,'cov': [next(cov_cycle) for _ in range(N)]
    }
    ,index=counts.columns
  )
  design = 'category[control] ~ cov[low] + counts'

  return CountMatrix(counts,column_data,design)

def logistic(counts_obj) :

  # avoid a statsmodels warning
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import statsmodels.api as sm

  # endog is the dependent variable
  endog = counts_obj.design_matrix.full_matrix['category__case']

  # exog is the right hand side
  exog = counts_obj.design_matrix.full_matrix.iloc[:,1:]

  coeffs = pandas.DataFrame(
    columns=exog.columns
    ,index=counts_obj.counts.index
    ,dtype='float64'
  )

  for gene in counts_obj.counts.index :

    exog['counts'] = counts_obj.counts.loc[gene]

    logit = sm.Logit(endog,exog)

    result = logit.fit()

    coeffs.loc[gene] = result.params

  return coeffs

def test_firth(logistic_test_counts_obj) :

  from de_toolkit.de import firth_logistic_regression

  logistic_test_counts_obj.design = 'category[control] ~ counts'

  coeffs = logistic(logistic_test_counts_obj)

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

  # the beta estimates can be within 1% of each other
  rtol=1e-2
  assert numpy.allclose(coeffs['Intercept'],firth_out['int__beta'],rtol=rtol)
  assert numpy.allclose(coeffs['counts'],firth_out['counts__beta'],rtol=rtol)

def test_firth_w_cov(logistic_test_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  logistic_test_counts_obj.design = 'category[control] ~ cov[low] + counts'

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

  coeffs = logistic(logistic_test_counts_obj)

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

  # the beta estimates can be within 1% of each other
  rtol=1e-2
  assert numpy.allclose(coeffs['Intercept'],firth_out['int__beta'],rtol=rtol)
  assert numpy.allclose(coeffs['cov__high'],firth_out['cov__high__beta'],rtol=rtol)
  assert numpy.allclose(coeffs['counts'],firth_out['counts__beta'],rtol=rtol)

@pytest.mark.skip(reason='test takes a long time, only turn on periodically')
def test_firth_w_big_data_cov(fake_big_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

@pytest.mark.skip(reason='test takes a long time, only turn on periodically')
def test_firth_w_huge_data_cov(fake_huge_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_huge_counts_obj.add_design('category ~ cont_cov')

  firth_out = firth_logistic_regression(fake_huge_counts_obj)
