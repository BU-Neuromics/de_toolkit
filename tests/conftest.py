from contextlib import contextmanager
import csv
import os
import pandas
import pytest
from subprocess import Popen
import tempfile

@pytest.fixture
def check_exit_status() :
  def f(cmd,exits=[0]):
    p = Popen(cmd,shell=True)
    p.communicate()
    return p.returncode in exits
  return f

# fixture tree:
# fake_counts_text_data
#   -> fake_counts_csv
#   -> fake_counts_tsv
#   -> fake_counts_obj
#   -> fake_counts_pandas_dataframe
#     -> fake_counts_numpy_matrix
# fake_big_counts
#   -> fake_big_counts_csv
#   -> fake_big_counts_obj
# fake_design
# fake_column_data
#   -> fake_column_data_pandas_dataframe
#   -> fake_column_data_csv

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
def fake_counts_csv(request,fake_counts_text_data) :
  with temp_csv_wrap(fake_counts_text_data,',') as f :
    yield f.name

@pytest.fixture()
def fake_counts_tsv(request,fake_counts_text_data) :
  with temp_csv_wrap(fake_counts_text_data,'\t') as f :
    yield f.name

@pytest.fixture()
def fake_big_counts_csv(request,fake_big_counts_data) :
  with temp_csv_wrap(fake_big_counts_data,',') as f :
    yield f.name

@pytest.fixture()
def fake_column_data(request) :
  covs = [
    ['sample','category','cont_cov']
    ,['a','case',0.1]
    ,['b','case',1.0]
    ,['c','cont',10.0]
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
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter='\t')
    for r in fake_column_data :
      tmp_f.writerow(r)

  yield f.name

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

