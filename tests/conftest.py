from contextlib import contextmanager
import csv
import os
import pandas
import pytest
from subprocess import Popen
import tempfile

################################################################################
# utility functions
@pytest.fixture
def check_exit_status() :
  def f(cmd,exits=[0]):
    p = Popen(cmd,shell=True)
    p.communicate()
    return p.returncode in exits
  return f

################################################################################

################################################################################
# fixtures

# fixture tree:

# fake_column_data - 20 samples, one categorical, one continuous cov
#   -> fake_column_data_pandas_dataframe
#   -> fake_column_data_csv

# fake_huge_column_data - 26 samples, one categorical, one continuous cov
#   -> fake_huge_column_data_pandas_dataframe
#   -> fake_huge_column_data_csv

# fake_counts_text_data - 6 genes, 3 samples (fake_column_data)
#   -> fake_counts_csv
#   -> fake_counts_tsv
#   -> fake_counts_obj
#   -> fake_counts_pandas_dataframe
#     -> fake_counts_numpy_matrix

# fake_counts_text_data_with_zeros - 6 genes, 3 samples (fake_column_data_with_zeros)
#   -> fake_counts_csv_with_zeros
#   -> fake_counts_tsv_with_zeros
#   -> fake_counts_obj_with_zeros
#   -> fake_counts_pandas_dataframe_with_zeros
#     -> fake_counts_numpy_matrix_with_zeros

# fake_count_list_data_coldist - 60 genes, 3 samples (test the coldist function)
#   -> fake_count_coldist_csv
#   -> fake_count_dist_pandas_dataframe
#   -> fake_count_dist_matrix
#   ->fake_count_coldist_obj

#  fake_count_list_data_rowdist - 3 genes, 20 samples (test the rowdist function)
#   -> fake_count_rowdist_csv
#   -> fake_count_rowdist_obj

# fake_big_counts - 1000 genes, 3 samples (fake_column_data)
#   -> fake_big_counts_csv
#   -> fake_big_counts_obj

# fake_huge_counts - 30000 genes, 26 samples (fake_huge_column_data)
#   -> fake_huge_counts_csv
#   -> fake_huge_counts_obj

# fake_logistic_design

################################################################################


################################################################################
# fake_column_data

@pytest.fixture()
def fake_column_data(request) :
  covs = [
    ['sample','category','cont_cov']
    ,['a','case',0.1]
    ,['b','case',1.0]
    ,['c','cont',10.0]
#    ,['d','case',1.0]
#    ,['e','case',1.0]
#    ,['f','case',1.0]
#    ,['g','case',1.0]
#    ,['h','case',1.0]
#    ,['i','case',1.0]
#    ,['j','case',1.0]
#    ,['k','case',1.0]
#    ,['l','case',1.0]
#    ,['m','case',1.0]
#    ,['n','case',1.0]
#    ,['o','case',1.0]
#    ,['p','case',1.0]
#    ,['q','case',1.0]
#    ,['r','case',1.0]
#    ,['s','case',1.0]
#    ,['t','case',1.0]
  ]
  return covs

@pytest.fixture()
def fake_column_data_pandas_dataframe(fake_column_data):
  data = fake_column_data
  covs = pandas.DataFrame(data[1:],columns=data[0])
  covs.index = covs['sample']
  return covs

@pytest.fixture()
def fake_column_data_csv(request,fake_column_data) :
  with temp_csv_wrap(fake_column_data,',') as f :
    yield f.name

################################################################################

################################################################################
# fake_column_data

@pytest.fixture()
def fake_huge_column_data(request) :
  import math
  import random
  import string
  names = string.ascii_lowercase
  covs = [
    ['sample','category','cont_cov','const_cov']
  ]+list(zip(
    names
    ,['case']*math.floor(len(names)/2)+['cont']*math.ceil(len(names)/2)
    ,[10*random.random() for _ in names]
    ,[1 for _ in names]
  ))
  return covs

@pytest.fixture()
def fake_huge_column_data_pandas_dataframe(fake_huge_column_data):
  data = fake_huge_column_data
  covs = pandas.DataFrame(data[1:],columns=data[0])
  covs.index = covs['sample']
  return covs

@pytest.fixture()
def fake_huge_column_data_csv(request,fake_huge_column_data) :
  with temp_csv_wrap(fake_huge_column_data,',') as f :
    yield f.name

################################################################################

################################################################################
# fake_counts_data

@pytest.fixture()
def fake_counts_text_data() :
  data = [
    ['gene','a','b','c']
    ,['gene1','2.0','4.0','8.0']
    ,['gene2','3.0','9.0','27.0']
    ,['gene3','4.0','16.0','64.0']
    ,['gene4','5.0','25.0','125.0']
    ,['gene5','6.0','36.0','216.0']
  ]
  return data

@pytest.fixture()
def fake_counts_pandas_dataframe(fake_counts_csv) :
  return pandas.read_csv(fake_counts_csv
    ,index_col=0
  )

@pytest.fixture()
def fake_counts_numpy_matrix(fake_counts_pandas_dataframe) :
  return fake_counts_pandas_dataframe.as_matrix()

@pytest.fixture()
def fake_counts_csv(request,fake_counts_text_data) :
  with temp_csv_wrap(fake_counts_text_data,',') as f :
    yield f.name

@pytest.fixture()
def fake_counts_tsv(request,fake_counts_text_data) :
  with temp_csv_wrap(fake_counts_text_data,'\t') as f :
    yield f.name

@pytest.fixture
def fake_counts_obj(
  fake_counts_csv
  ,fake_column_data_csv
  ,fake_logistic_design) :

  return make_counts_obj(
    fake_counts_csv
    ,fake_column_data_csv
    ,fake_logistic_design
  )


################################################################################


################################################################################
# fake_counts_data_with_zeros

@pytest.fixture()
def fake_counts_text_data_with_zeros() :
  data = [
    ['gene','a','b','c']
    ,['gene1','2.0','4.0','0.0']
    ,['gene2','0.0','9.0','0.0']
    ,['gene3','4.0','0.0','0.0']
    ,['gene4','5.0','0.0','125.0']
    ,['gene5','6.0','36.0','216.0']
  ]
  return data

@pytest.fixture()
def fake_counts_pandas_dataframe_with_zeros(fake_counts_csv_with_zeros) :
  return pandas.read_csv(fake_counts_csv_with_zeros
    ,index_col=0
  )

@pytest.fixture()
def fake_counts_numpy_matrix_with_zeros(fake_counts_pandas_dataframe_with_zeros) :
  return fake_counts_pandas_dataframe_with_zeros.as_matrix()

@pytest.fixture()
def fake_counts_csv_with_zeros(request,fake_counts_text_data_with_zeros) :
  with temp_csv_wrap(fake_counts_text_data_with_zeros,',') as f :
    yield f.name

@pytest.fixture()
def fake_counts_tsv_with_zeros(request,fake_counts_text_data_with_zeros) :
  with temp_csv_wrap(fake_counts_text_data_with_zeros,'\t') as f :
    yield f.name

@pytest.fixture
def fake_counts_obj_with_zeros(
  fake_counts_csv_with_zeros
  ,fake_column_data_csv
  ,fake_logistic_design) :

  return make_counts_obj(
    fake_counts_csv_with_zeros
    ,fake_column_data_csv
    ,fake_logistic_design
  )

################################################################################


################################################################################
# big counts data

@pytest.fixture()
def fake_big_counts_data() :
  from numpy.random import negative_binomial, randint, uniform
  data = [
    ['gene','a','b','c']
  ]
  for i in range(1000) :
    n = randint(5,40)
    p = uniform(0.1,0.3)
    data.append([
      'gene{}'.format(i)
      ,negative_binomial(n,p)
      ,negative_binomial(n,p)
      ,negative_binomial(n,p)
    ])
  return data

#convert to csv from 2-D list
@pytest.fixture()
def fake_big_counts_csv(request,fake_big_counts_data) :
  with temp_csv_wrap(fake_big_counts_data,',') as f :
    yield f.name

#convert to pandas data frame from csv
@pytest.fixture()
def fake_big_counts_pandas_dataframe(fake_big_counts_csv) :
  return pandas.read_csv(fake_big_counts_csv
    ,index_col=0
  )

#convert to matrix from pandas data frame
@pytest.fixture()
def fake_big_counts_matrix(fake_big_counts_pandas_dataframe) :
  return fake_big_counts_pandas_dataframe.as_matrix()


@pytest.fixture
def fake_big_counts_obj(
  fake_big_counts_csv
  ,fake_column_data_csv
  ,fake_logistic_design) :

  return make_counts_obj(
    fake_big_counts_csv
    ,fake_column_data_csv
    ,fake_logistic_design
  )

print(fake_big_counts_obj)
################################################################################


################################################################################
# realistic (huge) counts data
@pytest.fixture()
def fake_huge_counts_data() :
  from numpy.random import negative_binomial, randint, uniform
  import string
  data = [
    ['gene']+list(string.ascii_lowercase)
  ]
  for i in range(30000) :
    n = randint(5,40)
    p = uniform(0.1,0.3)
    data.append(['gene{}'.format(i)]+
      [negative_binomial(n,p) for _ in range(len(string.ascii_lowercase))]
    )
  return data

@pytest.fixture()
def fake_huge_counts_csv(request,fake_huge_counts_data) :
  with temp_csv_wrap(fake_huge_counts_data,',') as f :
    yield f.name

@pytest.fixture
def fake_huge_counts_obj(
  fake_huge_counts_csv
  ,fake_column_data_csv
  ,fake_logistic_design) :

  return make_counts_obj(
    fake_huge_counts_csv
    ,fake_column_data_csv
    ,fake_logistic_design
  )

################################################################################


@contextmanager
def temp_csv_wrap(data,sep) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter=sep)
    for r in data :
      tmp_f.writerow(r)

  yield f

  # cleanup the csv
  os.remove(f.name)

@pytest.fixture()
def fake_gtf(request,fake_counts_text_data) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter='\t')
    for r in fake_counts_text_data :
      tmp_f.writerow(r)

  yield f.name

  # cleanup the csv
  os.remove(f.name)

@pytest.fixture()
def fake_logistic_design(request) :
  return 'category ~ counts'

@pytest.fixture()
def fake_nb_design(request) :
  return 'counts ~ category'

def make_counts_obj(
  counts_csv
  ,column_data_csv
  ,design=None) :
  from de_toolkit import CountMatrixFile

  counts_obj = CountMatrixFile(
    counts_csv
    ,column_data_csv
    ,design
  )

  return counts_obj

def pytest_namespace():
    return {
      'temp_csv_wrap': temp_csv_wrap
      ,'make_counts_obj': make_counts_obj
    }

