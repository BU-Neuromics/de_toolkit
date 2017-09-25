import numpy
import pandas
import pytest

@pytest.fixture
def model_data() :
  N = 100
  df = pandas.DataFrame({
    'cont': numpy.random.random(size=N),
    'binary_str': numpy.random.choice(['A','B'],size=N),
    'binary_int': numpy.random.choice([0,1],size=N),
    'cat_str': numpy.random.choice(list('ABCD'),size=N),
    'cat_int': numpy.random.choice([1,2,3,4],size=N)
  })
  return df

def test_patsy_lite_to_patsy(model_data) :
  from de_toolkit.patsy_lite import patsy_lite_to_patsy, PatsyLiteParseError
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

def test_DesignMatrix(model_data) :

  from de_toolkit.patsy_lite import DesignMatrix, ModelError

  dm = DesignMatrix('cont ~ binary_str[B] + binary_int + cat_int',model_data)
  assert dm.design == 'cont ~ Intercept + binary_str__A + binary_int + cat_int'
  assert dm.full_matrix.shape == (100,5)
  assert (dm.full_matrix['cont'] == model_data['cont']).all()
  assert (dm.full_matrix['binary_int'] == model_data['binary_int']).all()
  assert (dm.full_matrix['cat_int'] == model_data['cat_int']).all()

  with pytest.raises(ModelError) :
    dm.drop_from_lhs('oogabooga')

  with pytest.raises(ModelError) :
    dm.drop_from_rhs('oogabooga')

  # binary_str[A] is excluded on left
  dm = DesignMatrix('binary_str[B] ~ cont',model_data)
  assert dm.design == 'binary_str__A ~ Intercept + cont'

  # binary_str[A] is excluded on left, binary_int stays as is (not categorical)
  dm = DesignMatrix('binary_str[B] ~ cont + binary_int',model_data)
  assert dm.design == 'binary_str__A ~ Intercept + cont + binary_int'
  assert 'binary_int' in dm.rhs

  # cat_str[A] is missing from right
  dm = DesignMatrix('binary_str[B] ~ cont + cat_str[A]',model_data)
  assert dm.design == 'binary_str__A ~ Intercept + cat_str__B + cat_str__C + cat_str__D + cont'
  assert 'cat_str__A' not in dm.rhs

  # cat_str[B] is missing from right
  dm = DesignMatrix('binary_str[B] ~ cont + cat_str[B,C,D,A]',model_data)
  assert dm.design == 'binary_str__A ~ Intercept + cat_str__C + cat_str__D + cat_str__A + cont'
  assert 'cat_str__B' not in dm.rhs

  # cat_str[A] is missing from right
  dm = DesignMatrix('binary_str[A] ~ cont + cat_str[B,C,D,A]',model_data)
  assert dm.design == 'binary_str__B ~ Intercept + cat_str__C + cat_str__D + cat_str__A + cont'
  assert 'cat_str__A' not in dm.lhs

  # cat_str[A] is missing from right implicitly (no ref group set)
  dm = DesignMatrix('binary_str ~ cont + cat_str',model_data)
  assert dm.design == 'binary_str__B ~ Intercept + cat_str__B + cat_str__C + cat_str__D + cont'
  assert 'cat_str__A' not in dm.lhs

  # binary_str[A] and cat_str[A] missing from right implicitly
  dm = DesignMatrix('cont ~ binary_str + cat_str',model_data)
  assert dm.design == 'cont ~ Intercept + binary_str__B + cat_str__B + cat_str__C + cat_str__D'
  assert 'binary_str__A' not in dm.rhs
  assert 'cat_str__A' not in dm.rhs

  # whatever, people can do this at their own risk
  dm = DesignMatrix('cont ~ binary_str:cat_str',model_data)
  assert dm.design == ('cont ~ Intercept + cat_str__B + cat_str__C + cat_str__D + '
                       'binary_str__B:cat_str__A + binary_str__B:cat_str__B + '
                       'binary_str__B:cat_str__C + binary_str__B:cat_str__D')


