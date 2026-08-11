
from de_toolkit.common import CountMatrix, InvalidDesignException
from de_toolkit.de import main
from de_toolkit.wrapr import check_r, check_r_package

import docopt
from itertools import cycle
import numpy
import os
import pandas
import pytest
from tempfile import NamedTemporaryFile
import warnings

r_test = pytest.mark.skipif(not check_r(),
        reason='r is not installed, skipping test'
)
logistf_test = pytest.mark.skipif(not check_r_package('logistf'), 
        reason='logistf package not installed, skipping test'
)
deseq2_test = pytest.mark.skipif(not check_r_package('DESeq2'), 
        reason='DESeq2 package not installed, skipping test'
)

@deseq2_test
def test_R_check_names_nonsense(deseq2_test_counts_obj) :

    with NamedTemporaryFile() as f :
        out_fn = f.name

    main(['detk-de','deseq2','counts ~ RIN + Status[CNT]',
          'tests/de/R_check_names_counts.csv',
          'tests/de/R_check_names_meta.csv','-o',out_fn])

    from de_toolkit.de import deseq2

    # standard R functions like read.csv and data.frame call
    # check.names() on their rows and column names so that they are
    # "syntactically correct", which renames things with 'invalid'
    # characters in R, like '-', and probably '$'

    # the R scripts in detk need to be able to handle this
    # add invalid R characters to columns and rows
    cnts = deseq2_test_counts_obj.counts.copy()
    cnts.columns = [f'$-{_}' for _ in cnts.columns]

    covs = deseq2_test_counts_obj.column_data.copy()
    covs.index = [f'$-{_}' for _ in covs.index]

    counts_obj = CountMatrix(
            cnts,
            covs,
            'counts ~ cov[low] + category[control]'
    )

    # full model results
    res = deseq2(
            counts_obj,
            normalized=True,
            all_coeff_results=True,
            routput_dir='tmp_output'
        )

    # these counts have true lfc in range(-4,5)
    assert all(res.index == counts_obj.counts.index)

def test_de_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main()

@pytest.fixture
def deseq2_test_counts_obj() :
  N = 50
  N1 = int(N/2)
  N2 = N-N1
  # NB mean = pr/(1-p)
  # NB r = mean*(1-p)/p
  # NB var = pr/(1-p)**2
  base_p = 0.5 # base probability of success set to 0.5
  base_mean = 1000. # one group has a mean count of 1000
  base_r = base_mean*(1-base_p)/base_p

  # iterate different means for the other group
  real_lfc = range(-4,5)

  counts = pandas.DataFrame(
    columns=[f'sample{_}' for _ in range(N)]
    ,index=(f'gene{_}' for _ in range(len(real_lfc)))
    ,dtype='float64'
  )

  base_counts = numpy.random.negative_binomial(
    base_r,
    base_p,
    size=(len(real_lfc),N1)
  )

  counts.loc[:,counts.columns[:N1]] = base_counts

  for i,lfc in enumerate(real_lfc) :
    mean = base_mean*2**lfc
    lfc_r = mean*(1-base_p)/base_p
    counts.loc[counts.index[i],counts.columns[N1:N]] = numpy.random.negative_binomial(
            lfc_r,
            base_p,
            size=N2
    )

  cov_cycle = cycle(['high','low'])
  column_data = pandas.DataFrame({
      'category': ['control']*(N1)+['case']*(N2)
      ,'cov': [next(cov_cycle) for _ in range(N)]
      ,'cont_cov': [10*numpy.random.random() for _ in range(N)]
    }
    ,index=counts.columns
  )
  design = 'counts ~ cov[low] + category[control]'

  return CountMatrix(counts,column_data,design)

@r_test
@deseq2_test
def test_deseq2_cli(fake_counts_csv,fake_column_data_csv) :

    with NamedTemporaryFile() as f :
        out_fn = f.name

    main(['detk-de','deseq2','--gene-wise-disp','counts ~ category',fake_counts_csv,fake_column_data_csv,'-o',out_fn])

    orig_res = pandas.read_csv(fake_counts_csv)
    print(orig_res)
    res = pandas.read_csv(out_fn)
    print(res)
    assert all(res.gene == orig_res.gene)

    assert all(res.columns == [
                                'gene',
                                'baseMean',
                                'category__cont__log2FoldChange',
                                'category__cont__lfcSE',
                                'category__cont__stat',
                                'category__cont__pvalue',
                                'category__cont__padj'
                                ])

    os.remove(out_fn)

@r_test
@deseq2_test
def test_deseq2_cli_w_cov(deseq2_test_counts_obj) :

    with NamedTemporaryFile() as f :
        out_fn = f.name

        with NamedTemporaryFile() as counts_f :

            print(deseq2_test_counts_obj.counts)
            fake_counts_csv = counts_f.name
            deseq2_test_counts_obj.counts.to_csv(fake_counts_csv,index_label='gene')

            with NamedTemporaryFile() as covs_f :

                fake_column_data_csv = covs_f.name
                deseq2_test_counts_obj.column_data.to_csv(fake_column_data_csv,index_label='sample')

                main(['detk-de','deseq2','counts ~ cont_cov + category[control]',fake_counts_csv,fake_column_data_csv,'-o',out_fn])

                orig_res = pandas.read_csv(fake_counts_csv)
                res = pandas.read_csv(out_fn)
                assert all(res.gene == orig_res.gene)
                assert all(res.columns == [
                                            'gene',
                                            'baseMean',
                                            'cont_cov__log2FoldChange',
                                            'cont_cov__lfcSE',
                                            'cont_cov__stat',
                                            'cont_cov__pvalue',
                                            'cont_cov__padj',
                                            'category__case__log2FoldChange',
                                            'category__case__lfcSE',
                                            'category__case__stat',
                                            'category__case__pvalue',
                                            'category__case__padj'
                                            ])



@r_test
@deseq2_test
def test_deseq2_de(deseq2_test_counts_obj) :
    from de_toolkit.de import deseq2

    # full model results
    res = deseq2(
            deseq2_test_counts_obj,
            normalized=True,
            all_coeff_results=True
        )

    # these counts have true lfc in range(-4,5)
    assert all(res.index == deseq2_test_counts_obj.counts.index)
    assert numpy.allclose(res['category__case__log2FoldChange'],numpy.arange(-4,5),atol=0.2)

    # all coef results off
    res = deseq2(
            deseq2_test_counts_obj,
            normalized=True,
            all_coeff_results=False
        )
    # these counts have true lfc in range(-4,5)
    assert numpy.allclose(res['category__case__log2FoldChange'],numpy.arange(-4,5),atol=0.2)

    # with cores
    res = deseq2(
            deseq2_test_counts_obj,
            normalized=True,
            all_coeff_results=True,
            cores=2
        )
    # these counts have true lfc in range(-4,5)
    assert numpy.allclose(res['category__case__log2FoldChange'],numpy.arange(-4,5),atol=0.2)

    # test missing design situations
    with pytest.raises(InvalidDesignException) :
        res = deseq2(
                CountMatrix(
                    deseq2_test_counts_obj.counts,
                    deseq2_test_counts_obj.column_data,
                    None
                )
            )

    # test invalid design situations
    with pytest.raises(InvalidDesignException) :
        res = deseq2(
                CountMatrix(
                    deseq2_test_counts_obj.counts,
                    deseq2_test_counts_obj.column_data,
                    'category[control] ~ counts'
                )
            )

@r_test
@logistf_test
def test_firth_cli(fake_counts_csv,fake_column_data_csv) :
  main(['detk-de','firth','category ~ counts',fake_counts_csv,fake_column_data_csv])

@r_test
@logistf_test
def test_firth_cli_multicore(fake_counts_csv,fake_column_data_csv) :
  main(['detk-de','firth','--cores=2','category ~ counts',fake_counts_csv,fake_column_data_csv])

@r_test
@logistf_test
def test_firth_cli_w_cov(fake_counts_csv,fake_column_data_csv) :
  main(['detk-de','firth','category ~ cont_cov + counts',fake_counts_csv,fake_column_data_csv])

@pytest.fixture
def logistic_test_counts_obj() :
  N = 5000
  N1 = int(N/2)
  N2 = N-N1
  counts = pandas.DataFrame(
    columns=[f'gene{_}' for _ in range(N)]
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

# this function implements normal logistic regression via statsmodels
# for comparison with Firth logistic regression
# maybe move it inot the de.py module?
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

@r_test
@logistf_test
def test_firth(logistic_test_counts_obj) :

  from de_toolkit.de import firth_logistic_regression

  logistic_test_counts_obj.design = 'category[control] ~ counts'

  coeffs = logistic(logistic_test_counts_obj)

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

  # the beta estimates can be within 1% of each other
  atol=1e-2
  assert numpy.allclose(coeffs['Intercept'],firth_out['int__beta'],atol=atol)
  assert numpy.allclose(coeffs['counts'],firth_out['counts__beta'],atol=atol)

@r_test
@logistf_test
def test_firth_rda(logistic_test_counts_obj) :

  from de_toolkit.de import firth_logistic_regression

  logistic_test_counts_obj.design = 'category[control] ~ counts'

  # test with rda
  with NamedTemporaryFile() as f :
      firth_logistic_regression(
              logistic_test_counts_obj,
              rda=f.name
      )
      f.flush()

      assert len(f.read()) != 0

@r_test
@logistf_test
def test_firth_parallel(logistic_test_counts_obj) :

  from de_toolkit.de import firth_logistic_regression

  logistic_test_counts_obj.design = 'category[control] ~ counts'

  firth_logistic_regression(
          logistic_test_counts_obj,
          cores=2
  )

@r_test
@logistf_test
def test_firth_w_cov(logistic_test_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  logistic_test_counts_obj.design = 'category[control] ~ cov[low] + counts'

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

  coeffs = logistic(logistic_test_counts_obj)

  firth_out = firth_logistic_regression(logistic_test_counts_obj)

  # the beta estimates can be within 1% of each other
  atol=1e-1
  assert numpy.allclose(coeffs['Intercept'],firth_out['int__beta'],atol=atol)
  assert numpy.allclose(coeffs['cov__high'],firth_out['cov__high__beta'],atol=atol)
  assert numpy.allclose(coeffs['counts'],firth_out['counts__beta'],atol=atol)

@pytest.mark.skip(reason='test takes a long time, only turn on periodically')
def test_firth_w_big_data_cov(fake_big_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  firth_logistic_regression(logistic_test_counts_obj)

@pytest.mark.skip(reason='test takes a long time, only turn on periodically')
def test_firth_w_huge_data_cov(fake_huge_counts_obj) :
  from de_toolkit.de import firth_logistic_regression

  fake_huge_counts_obj.add_design('category ~ cont_cov')

  firth_logistic_regression(fake_huge_counts_obj)


