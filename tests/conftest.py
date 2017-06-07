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

# fake_design

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
    ,['d','case',1.0]
    ,['e','case',1.0]
    ,['f','case',1.0]
    ,['g','case',1.0]
    ,['h','case',1.0]
    ,['i','case',1.0]
    ,['j','case',1.0]
    ,['k','case',1.0]
    ,['l','case',1.0]
    ,['m','case',1.0]
    ,['n','case',1.0]
    ,['o','case',1.0]
    ,['p','case',1.0]
    ,['q','case',1.0]
    ,['r','case',1.0]
    ,['s','case',1.0]
    ,['t','case',1.0]
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
    ['sample','category','cont_cov']
  ]+list(zip(
    names
    ,['case']*math.floor(len(names)/2)+['cont']*math.ceil(len(names)/2)
    ,[10*random.random() for _ in names]
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
  ,fake_design) :

  return make_counts_obj(
    fake_counts_csv
    ,fake_column_data_csv
    ,fake_design
  )


################################################################################

################################################################################
# fake count data to test the coldist
@pytest.fixture()
def fake_count_list_data_coldist() :
  data = [
  ['gene','a','b','c'],
  ['gene1', 1, 2, 3],
  ['gene2', 1, 2, 3],
  ['gene3', 1, 2, 3],
  ['gene4', 6, 7, 8],
  ['gene5', 6, 7, 8],
  ['gene6', 6, 7, 8],
  ['gene7', 11, 12, 13],
  ['gene8', 11, 12, 13],
  ['gene9', 11, 12, 13],
  ['gene10', 16, 17, 18],
  ['gene11', 16, 17, 18],
  ['gene12', 16, 17, 18],
  ['gene13', 21, 22, 23],
  ['gene14', 21, 22, 23],
  ['gene15', 21, 22, 23],
  ['gene16', 26, 27, 28],
  ['gene17', 26, 27, 28],
  ['gene18', 26, 27, 28],
  ['gene19', 31, 32, 33],
  ['gene20', 31, 32, 33],
  ['gene21', 31, 32, 33],
  ['gene22', 36, 37, 38],
  ['gene23', 36, 37, 38],
  ['gene24', 36, 37, 38],
  ['gene25', 41, 42, 43],
  ['gene26', 41, 42, 43],
  ['gene27', 41, 42, 43],
  ['gene28', 46, 47, 48],
  ['gene29', 46, 47, 48],
  ['gene30', 46, 47, 48],
  ['gene31', 51, 52, 53],
  ['gene32', 51, 52, 53],
  ['gene33', 51, 52, 53],
  ['gene34', 56, 57, 58],
  ['gene35', 56, 57, 58],
  ['gene36', 56, 57, 58],
  ['gene37', 61, 62, 63],
  ['gene38', 61, 62, 63],
  ['gene39', 61, 62, 63],
  ['gene40', 66, 67, 68],
  ['gene41', 66, 67, 68],
  ['gene42', 66, 67, 68],
  ['gene43', 71, 72, 73],
  ['gene44', 71, 72, 73],
  ['gene45', 71, 72, 73],
  ['gene46', 76, 77, 78],
  ['gene47', 76, 77, 78],
  ['gene48', 76, 77, 78],
  ['gene49', 81, 82, 83],
  ['gene50', 81, 82, 83],
  ['gene51', 81, 82, 83],
  ['gene52', 86, 87, 88],
  ['gene53', 86, 87, 88],
  ['gene54', 86, 87, 88],
  ['gene55', 91, 92, 93],
  ['gene56', 91, 92, 93],
  ['gene57', 91, 92, 93],
  ['gene58', 96, 97, 98],
  ['gene59', 96, 97, 98],
  ['gene60', 96, 97, 98]
  ]
  return data


#convert to csv from 2-D list
@pytest.fixture()
def fake_count_coldist_csv(request,fake_count_list_data_coldist) :
  with temp_csv_wrap(fake_count_list_data_coldist,',') as f :
    yield f.name

#convert to pandas data frame from csv
@pytest.fixture()
def fake_count_dist_pandas_dataframe(fake_count_coldist_csv) :
  return pandas.read_csv(fake_count_coldist_csv
    ,index_col=0
  )

#convert to matrix from pandas data frame
@pytest.fixture()
def fake_count_dist_matrix(fake_count_dist_pandas_dataframe) :
  return fake_count_dist_pandas_dataframe.as_matrix()


@pytest.fixture
def fake_count_coldist_obj(
  fake_count_coldist_csv
  ,fake_column_data_csv
  ,fake_design) :

  return make_counts_obj(
    fake_count_coldist_csv
    ,fake_column_data_csv
    ,fake_design
  )

################################################################################

################################################################################
# fake count data to test the rowdist
@pytest.fixture()
def fake_count_list_data_rowdist() :
  data = [
  [ 'gene', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
  [ 'gene1', 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39],
  [ 'gene2', 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40],
  [ 'gene3', 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41]
  ]
  return data


#convert to csv from 2-D list
@pytest.fixture()
def fake_count_rowdist_csv(request,fake_count_list_data_rowdist) :
  with temp_csv_wrap(fake_count_list_data_rowdist,',') as f :
    yield f.name


@pytest.fixture
def fake_count_rowdist_obj(
  fake_count_rowdist_csv
  ,fake_column_data_csv
  ,fake_design) :

  return make_counts_obj(
    fake_count_rowdist_csv
    ,fake_column_data_csv
    ,fake_design
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
def fake_counts_numpy_matrix(fake_counts_pandas_dataframe_with_zeros) :
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
  ,fake_design) :

  return make_counts_obj(
    fake_counts_csv_with_zeros
    ,fake_column_data_csv
    ,fake_design
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
  ,fake_design) :

  return make_counts_obj(
    fake_big_counts_csv
    ,fake_column_data_csv
    ,fake_design
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
  ,fake_design) :

  return make_counts_obj(
    fake_huge_counts_csv
    ,fake_column_data_csv
    ,fake_design
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
def fake_design(request) :
  return '~ category'

def make_counts_obj(
  counts_csv
  ,column_data_csv
  ,design) :
  from de_toolkit import CountMatrixFile

  counts_obj = CountMatrixFile(
    counts_csv
    ,column_data_csv
    ,design
  )

  return counts_obj
