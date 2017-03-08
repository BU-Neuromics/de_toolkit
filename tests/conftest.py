import csv
import os
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

@pytest.fixture(scope='session')
def fake_counts_data() :
  data = [
    ['gene','a','b','c']
    ,['gene1','2.0','4.0','8.0']
    ,['gene2','3.0','9.0','27.0']
    ,['gene3','4.0','16.0','64.0']
  ]
  return data

@pytest.fixture(scope='session')
def fake_counts_csv(request) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f)
    for r in fake_counts_data() :
      tmp_f.writerow(r)

  yield f.name

  # cleanup the csv
  os.remove(f.name)

@pytest.fixture(scope='session')
def fake_counts_tsv(request) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter='\t')
    for r in fake_counts_data() :
      tmp_f.writerow(r)

  yield f.name

  # cleanup the csv
  os.remove(f.name)

@pytest.fixture(scope='session')
def fake_gtf(request) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter='\t')
    for r in fake_counts_data() :
      tmp_f.writerow(r)

  yield f.name

  # cleanup the csv
  os.remove(f.name)
