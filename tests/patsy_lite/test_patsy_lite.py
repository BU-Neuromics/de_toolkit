import pytest
from de_toolkit.patsy_lite import patsy_lite_to_patsy, PatsyLiteParseError, build_design_matrix

def test_patsy_lite_to_patsy() :
  pltp = patsy_lite_to_patsy
  assert pltp('A ~ B').describe() == 'A ~ B'
  assert pltp('A~B').describe() == 'A ~ B'
  assert pltp('A[one]~B[two]').describe() == "C(A, Treatment('one')) ~ C(B, Treatment('two'))"
  assert pltp('A[one,two] ~ B').describe() == "C(A, levels=['one', 'two']) ~ B"
  assert pltp('A[one,two] ~ B + C').describe() == "C(A, levels=['one', 'two']) ~ B + C"
  assert (pltp('A[one,two] ~ B + C[case,control]').describe() ==
    "C(A, levels=['one', 'two']) ~ B + C(C, levels=['case', 'control'])"
  )
  with pytest.raises(PatsyLiteParseError) :
    pltp('B')
  with pytest.raises(PatsyLiteParseError) :
    pltp('A[one]~B[two]&C[three,four]')
  assert pltp('count ~ RIN + age_at_death').describe() == "count ~ RIN + age_at_death"

  # test patsy passthrough
  assert (pltp('np.log(x) ~ category[cont]').describe() == 
    "np.log(x) ~ C(category, Treatment('cont'))")

  assert (pltp('np.log(x) ~ a:b + category[cont]').describe() == 
    "np.log(x) ~ a:b + C(category, Treatment('cont'))")

  assert (pltp('1 + np.log(x) ~ 1 + category[cont]').describe() == 
    "1 + np.log(x) ~ C(category, Treatment('cont'))")

  assert (pltp('np.log(x) ~ -1 + category[cont]').describe() == 
    "np.log(x) ~ 0 + C(category, Treatment('cont'))")

def test_build_design_matrix(fake_column_data_pandas_dataframe) :
  dm = build_design_matrix('category[cont] ~ cont_cov',fake_column_data_pandas_dataframe)
  print('\n\n\n----------------------------------------\n\n\n')
  dm = build_design_matrix('cont_cov ~ category[cont] + category:cont_cov',fake_column_data_pandas_dataframe)
  print('\n\n\n----------------------------------------\n\n\n')
  dm = build_design_matrix('cont_cov ~ category[cont] + category:category',fake_column_data_pandas_dataframe)
  assert False
