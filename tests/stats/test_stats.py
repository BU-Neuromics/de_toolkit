import docopt
import numpy as np
import os
import pandas
from pprint import pprint
import pytest
import tempfile
import json
import math
from de_toolkit.common import *
from de_toolkit.stats import *

################################################################################
@pytest.fixture
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
################################################################################

################################################################################
# fake count data to test the rowzero
################################################################################

def test_stats_cli(fake_counts_csv) :
  from de_toolkit.stats import main
  from docopt import DocoptExit
  with tempfile.TemporaryDirectory() as d :
      for cmd in ('summary','basestats','coldist','rowdist','colzero','rowzero','entropy') :
          with pytest.raises(DocoptExit) :
              main(['detk-stats',cmd])
          main(['detk-stats',cmd,fake_counts_csv,'--report-dir={}'.format(d)])

################################################################################
# base tests
#test for base function
def test_stats_base(fake_counts_obj):
    output = BaseStats(fake_counts_obj)
    assert output.properties['num_cols'] == 3
    assert output.properties['num_rows'] == 5
    assert output.name == 'basestats'

#test that json output for base function is correct
def test_stats_base_json(fake_counts_obj):
    output = BaseStats(fake_counts_obj)

    json_output = output.json

    assert json_output.get('name') == 'basestats'
    assert json_output.get('properties', {}).get('num_cols') == 3
    assert json_output.get('properties', {}).get('num_rows') == 5

def test_stats_base_output(fake_counts_obj):
    output = BaseStats(fake_counts_obj)
    assert output.output == [['stat','val'],['num_cols',3],['num_rows',5]]

################################################################################
# coldist tests
# fake count data to test the coldist
@pytest.fixture
def fake_count_list_data_coldist() :
  data = [
      ['gene','a','b','c']
  ]
  for i in range(100) :
      data.append(['gene{}'.format(i)]+[i]*3)
  return data


#convert to csv from 2-D list
@pytest.fixture
def fake_count_coldist_csv(request,fake_count_list_data_coldist) :
  with pytest.temp_csv_wrap(fake_count_list_data_coldist,',') as f :
    yield f.name

#convert to pandas data frame from csv
@pytest.fixture
def fake_count_dist_pandas_dataframe(fake_count_coldist_csv) :
  return pandas.read_csv(fake_count_coldist_csv
    ,index_col=0
  )

#convert to matrix from pandas data frame
@pytest.fixture
def fake_count_dist_matrix(fake_count_dist_pandas_dataframe) :
  return fake_count_dist_pandas_dataframe.as_matrix()

@pytest.fixture
def fake_design() :
  pass

@pytest.fixture
def fake_count_coldist_obj(
  fake_count_coldist_csv
  ,fake_column_data_csv
  ,fake_design) :

  return pytest.make_counts_obj(
    fake_count_coldist_csv
    ,fake_column_data_csv
    ,fake_design
  )

#test that coldist function gets correct column names
def test_stats_coldist_params(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, 20, False, False)

    assert output.params['bins'] == 20
    assert output.params['log'] == False
    assert output.params['density'] == False

def test_stats_coldist_names(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, 20, False, False)
    col_dists = output['dists']
    col_name_func = [d['name'] for d in col_dists]

    col_name_true = ['a','b','c']
    assert col_name_func == col_name_true

#test that coldist function has the correct pct values
def test_stats_coldist_pct(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, 20, False, False)
    col_pct = output['pct']
    assert all(col_pct == list(_/20 for _ in range(20)))

#test that coldist function gets correct column dist
def test_stats_coldist_dist(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, bins=10)
    col_dists = output['dists']
    col_dist_func = [[_[1] for _ in d['dist']] for d in col_dists]
    col_dist_true = [[10.0 for i in range(10)] for j in range(3)]
    assert col_dist_func == col_dist_true

#test that coldist function gets correct column dist
def test_stats_coldist_pctVal(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, bins=10)
    col_dists = [_['percentiles'] for _ in output['dists']]

    coldist_pct = [_[0] for _ in col_dists[0]]
    assert coldist_pct == [_/10. for _ in range(10)]

    coldist_pctVal = [_[1] for _ in col_dists[0]]
    coldist_true = [(i*(10-0.1)) for i in range(10)]
    assert np.allclose(coldist_pctVal,coldist_true)

#test that coldist function gets correct column dist
def test_stats_coldist_log_pctVal(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, bins=10, log=True)
    col_dists = [_['percentiles'] for _ in output['dists']]

    coldist_pct = [_[0] for _ in col_dists[0]]
    assert coldist_pct == [_/10. for _ in range(10)]

    coldist_pctVal = [_[1] for _ in col_dists[0]]
    coldist_true = np.percentile(
            np.log10(fake_count_coldist_obj.counts.a+1),
            np.arange(10)*10
    )
    assert np.allclose(coldist_pctVal,coldist_true)

#test that coldist function with density option gets correct dists
def test_stats_coldist_density(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, 99, density=True)
    col_dists = output['dists']
    col_dist_sums = [sum(_[1] for _ in d['dist']) for d in col_dists]

    col_dist_true = [1.0 for i in range(3)]

    assert np.allclose(col_dist_sums,col_dist_true)

#test that coldist function get correct number of bins
def test_stats_coldist_bins(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, bins=5)
    col_dists = output['dists']
    col_dist_bins = [[_[0] for _ in d['dist']] for d in col_dists]
    num_bins = [len(b) for b in col_dist_bins]
    true_bins = [5, 5, 5]

    assert num_bins == true_bins

#test log option for coldist function
def test_stats_coldist_log_bins(fake_count_coldist_obj):
    # the counts go from 0 to 99, make them go from 1 to 100 to make testing
    # easier
    fake_count_coldist_obj.counts = fake_count_coldist_obj.counts+1
    output = ColDist(fake_count_coldist_obj, bins=2, log=True)
    col_dists = output['dists']
    col_dist_bins = [_[0] for _ in col_dists[0]['dist']]
    true_dists, true_bins = np.histogram(
            np.log10(fake_count_coldist_obj.counts.a+1),
            bins=2
    )
    assert np.allclose(col_dist_bins,true_bins[:-1])

    col_dist_func = [[_[1] for _ in d['dist']] for d in col_dists]
    true_dists = [[13,100-13]]*3
    assert col_dist_func==true_dists

#test that json output for coldist function is correct
def test_stats_coldist_json(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, bins=10)

    json_output = output.json

    name = json_output.get('name')
    dists = json_output.get('properties', {}).get('dists')

    true_pct = [10*x for x in range(1, 11)]

    true_col_names = ['a', 'b', 'c']
    col_names = []
    for i in range(0, len(dists)):
        dist = dists[i]
        col_name = dist['name']
        col_names.append(col_name)

    col_dists = json_output.get('properties').get('dists')
    col_dist_func = [[_[1] for _ in d['dist']] for d in col_dists]
    col_dist_true = [[10.0 for i in range(10)] for j in range(3)]

    assert name=='coldist'
    assert true_col_names==col_names
    assert col_dist_func==col_dist_true

    coldist_pctVal = [_[1] for _ in col_dists[0]['percentiles']]
    coldist_true = np.percentile(
            fake_count_coldist_obj.counts.a,
            np.arange(10)*10
    )
    assert np.allclose(coldist_pctVal,coldist_true)

def test_stats_coldist_output(fake_count_coldist_obj):
    # the counts go from 0 to 99, make them go from 1 to 100 to make testing
    # easier
    fake_count_coldist_obj.counts = fake_count_coldist_obj.counts+1
    output = ColDist(fake_count_coldist_obj, bins=2)

    colnames = []
    for col in fake_count_coldist_obj.counts.columns :
        for colstat in ('binstart','bincount','pct','pctVal') :
            colnames.append('{}__{}'.format(col,colstat))
    assert output.output[0] == colnames

################################################################################
# rowdist tests
@pytest.fixture
def fake_count_list_data_rowdist() :
  data = [['gene']+['s{}'.format(_) for _ in range(100)]]
  for i in range(3) :
      data.append(['gene{}'.format(i+1)]+[_+1 for _ in range(100)])
  return data

@pytest.fixture
def fake_column_data_rowdist(fake_count_list_data_rowdist) :
    sample_names = fake_count_list_data_rowdist[0]
    sample_names[0] = 'sampleId'
    col = ['cov']
    for i in range(len(sample_names)-1) :
        col.append(['case','control'][i%2])
    return list(zip(sample_names,col))

#convert to csv from 2-D list
@pytest.fixture
def fake_count_rowdist_csv(request,fake_count_list_data_rowdist) :
  with pytest.temp_csv_wrap(fake_count_list_data_rowdist,',') as f :
    yield f.name

@pytest.fixture
def fake_column_data_rowdist_csv(request,fake_column_data_rowdist) :
  with pytest.temp_csv_wrap(fake_column_data_rowdist,',') as f :
    yield f.name

@pytest.fixture
def fake_count_rowdist_obj(
  fake_count_rowdist_csv
  ,fake_column_data_rowdist_csv
  ,fake_design) :

  return pytest.make_counts_obj(
    fake_count_rowdist_csv
    ,fake_column_data_rowdist_csv
    ,fake_design
  )

#test that rowdist function gets correct rowumn names
def test_stats_rowdist_params(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, 20, False, False)

    assert output.params['bins'] == 20
    assert output.params['log'] == False
    assert output.params['density'] == False

#test that rowdist function gets correct row names
def test_stats_rowdist_names(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, 20, False, False)
    row_dists = output['dists']
    row_name_func = [d['name'] for d in row_dists]

    row_name_true = ['gene1','gene2','gene3']
    assert row_name_func == row_name_true

#test that rowdist function has the correct pct values
def test_stats_rowdist_pct(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, 20, False, False)
    row_pct = output['pct']
    assert row_pct == list((_+1)/.2 for _ in range(20))

#test that rowdist function gets correct row dists
def test_stats_rowdist_dist(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, bins=10)
    row_dists = output['dists']
    row_dist_func = [d['dist'] for d in row_dists]
    row_dist_true = [[10.0 for i in range(10)] for j in range(3)]
    assert row_dist_func == row_dist_true

#test that rowdist function with density option gets correct dists
def test_stats_rowdist_density(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, 99, False, True)
    row_dists = output['dists']
    row_dist_func = [d['dist'] for d in row_dists]
    row_dist_sums = [sum(x) for x in row_dist_func]

    row_dist_true = [1.0 for i in range(3)]

    assert np.allclose(row_dist_sums,row_dist_true)

#test that rowdist function get correct number of bins
def test_stats_rowdist_bins(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, 5, False, False)
    row_dists = output['dists']
    row_dist_bins = [d['bins'] for d in row_dists]
    num_bins = [len(b) for b in row_dist_bins]
    true_bins = [5, 5, 5]

    assert num_bins == true_bins

#test log option for rowdist function
def test_stats_rowdist_bins(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, bins=2, log=True)
    row_dists = output['dists']
    row_dist_bins = [d['bins'] for d in row_dists]
    row_dist_func = [d['dist'] for d in row_dists]
    true_bins = [[1,2]]*3
    true_dists = [[9,91]]*3
    assert row_dist_bins==true_bins
    assert row_dist_func==true_dists

#test that json output for rowdist function is correct
def test_stats_rowdist_json(fake_count_rowdist_obj):

    output = RowDist(fake_count_rowdist_obj, bins=2, log=True)

    json_output = output.json

    name = json_output.get('name')
    pct = json_output.get('properties', {}).get('pct')
    dists = json_output.get('properties', {}).get('dists')    

    true_pct = [50,100]

    true_row_names = ['gene1', 'gene2', 'gene3']
    row_names = []
    for i in range(0, len(dists)):
        dist = dists[i]
        row_name = dist['name']
        row_names.append(row_name)

    row_dist_func = [d['dist'] for d in dists]

    true_bins = [[1,2]]*3
    row_dist_true = [[9,91]]*3

    assert name=='rowdist'
    assert pct==true_pct
    assert true_row_names==row_names
    assert row_dist_func==row_dist_true

def test_stats_rowdist_output(fake_count_rowdist_obj):
    output = RowDist(fake_count_rowdist_obj, bins=2)
    assert output.output[0] == ['rowname','bin_50.0','bin_100.0','dist_50.0','dist_100.0']
    assert output.output[1] == ['gene1', 50.5, 100, 50, 50]

################################################################################
# colzero tests
#test that colzero function gets correct column names
def test_stats_colzero_names(fake_counts_obj_with_zeros):
    output = ColZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_col_names = ['a', 'b', 'c']

    col_names = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        name = col.get('name')
        col_names.append(name)

    assert true_col_names==col_names

#test that colzero function gets correct zero counts
def test_stats_colzero_zero_counts(fake_counts_obj_with_zeros):
    output = ColZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_zero_counts = [1, 2, 3]

    zero_counts = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        zero_count = col.get('zero_count')
        zero_counts.append(zero_count)

    assert true_zero_counts==zero_counts

#test that colzero function gets correct zero fractions
def test_stats_colzero_zero_fracs(fake_counts_obj_with_zeros):
    output = ColZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_zero_fracs = [1/5, 2/5, 3/5]

    zero_fracs = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        zero_frac = col.get('zero_frac')
        zero_fracs.append(zero_frac)

    assert true_zero_fracs == zero_fracs

#test that colzero function gets correct column means
def test_stats_colzero_col_means(fake_counts_obj_with_zeros):
    output = ColZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_col_means = [(2+4+5+6)/5, (4+9+36)/5, (125+216)/5]

    col_means = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        col_mean = col.get('mean')
        col_means.append(col_mean)

    assert true_col_means == col_means

#test that colzero function gets correct nonzero column means
def test_stats_colzero_nonzero_col_means(fake_counts_obj_with_zeros):
    output = ColZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_nonzero_col_means = [(2+4+5+6)/4, (4+9+36)/3, (125+216)/2]

    nonzero_col_means = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        nonzero_col_mean = col.get('nonzero_mean')
        nonzero_col_means.append(nonzero_col_mean)

    assert true_nonzero_col_means == nonzero_col_means

#test that json output for colzero function is correct
def test_stats_colzero_json(fake_counts_obj_with_zeros):

    output = ColZero(fake_counts_obj_with_zeros)

    json_output = output.json
    name = json_output.get('name')
    zeros = json_output.get('properties', {}).get('zeros')

    true_col_names = ['a', 'b', 'c']

    col_names = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        col_name = col.get('name')
        col_names.append(col_name)
    
    true_zero_counts = [1, 2, 3]

    zero_counts = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        zero_count = col.get('zero_count')
        zero_counts.append(zero_count)
    
    true_zero_fracs = [1/5, 2/5, 3/5]

    zero_fracs = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        zero_frac = col.get('zero_frac')
        zero_fracs.append(zero_frac)

    true_col_means = [(2+4+5+6)/5, (4+9+36)/5, (125+216)/5]

    col_means = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        col_mean = col.get('mean')
        col_means.append(col_mean)

    true_nonzero_col_means = [(2+4+5+6)/4, (4+9+36)/3, (125+216)/2]

    nonzero_col_means = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        nonzero_col_mean = col.get('nonzero_mean')
        nonzero_col_means.append(nonzero_col_mean)

    assert name=='colzero'
    assert true_col_names==col_names
    assert true_zero_counts==zero_counts
    assert true_zero_fracs == zero_fracs
    assert true_col_means==col_means
    assert true_nonzero_col_means==nonzero_col_means

def test_stats_colzero_output(fake_counts_obj_with_zeros):
    output = ColZero(fake_counts_obj_with_zeros)
    assert output.output[0] == [
            'name','zero_count','zero_frac',
            'mean','median','nonzero_mean','nonzero_median'
        ]
    assert output.output[1] == ['a', 1, 0.2, 3.4, 4, 4.25, 4.5]
    assert output.output[2][:2] == ['b', 2]
    assert output.output[3][:2] == ['c', 3]

################################################################################
# rowzero tests
@pytest.fixture
def fake_count_list_data_rowzero() :
  data = [
  [ 'gene', 'a', 'b', 'c', 'd', 'e'],
  [ 'gene1', 1, 3, 5, 7, 9],
  [ 'gene2', 2, 4, 6, 8, 10],
  [ 'gene3', 0, 0, 0, 0, 0]
  ]
  return data


#convert to csv from 2-D list
@pytest.fixture
def fake_count_rowzero_csv(request,fake_count_list_data_rowzero) :
  with pytest.temp_csv_wrap(fake_count_list_data_rowzero,',') as f :
    yield f.name


@pytest.fixture
def fake_count_rowzero_obj(
  fake_count_rowzero_csv
  ,fake_column_data_csv
  ,fake_design) :

  return pytest.make_counts_obj(
    fake_count_rowzero_csv
    ,fake_column_data_csv
    ,fake_design
  )

#test that rowzero function gets correct row names
def test_stats_rowzero_names(fake_counts_obj_with_zeros):
    output = RowZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_row_names = ['gene1', 'gene2', 'gene3', 'gene4', 'gene5']

    row_names = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        row_name = row.get('name')
        row_names.append(row_name)

    assert true_row_names == row_names

#test that rowzero function gets correct zero counts
def test_stats_rowzero_zero_counts(fake_counts_obj_with_zeros):
    output = RowZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_zero_counts = [1, 2, 2, 1, 0]

    zero_counts = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        zero_count = row.get('zero_count')
        zero_counts.append(zero_count)

    assert true_zero_counts == zero_counts

#test that rowzero function gets correct zero fractions
def test_stats_rowzero_zero_fracs(fake_counts_obj_with_zeros):
    output = RowZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_zero_fracs = [1/3, 2/3, 2/3, 1/3, 0]

    zero_fracs = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        zero_frac = row.get('zero_frac')
        zero_fracs.append(zero_frac)

    assert true_zero_fracs == zero_fracs

#test that rowzero function gets correct row means
def test_stats_rowzero_row_means(fake_counts_obj_with_zeros):
    output = RowZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_row_means = [(2+4)/3, 9/3, 4/3, (5+125)/3, (6+36+216)/3]

    row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        row_mean = row.get('mean')
        row_means.append(row_mean)

    assert true_row_means == row_means

#test that rowzero function gets correct nonzero row means
def test_stats_rowzero_row_means(fake_counts_obj_with_zeros):
    output = RowZero(fake_counts_obj_with_zeros)
    zeros = output['zeros']

    true_nonzero_row_means = [(2+4)/2, 9, 4, (5+125)/2, (6+36+216)/3]

    nonzero_row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        nonzero_row_mean = row.get('nonzero_mean')
        nonzero_row_means.append(nonzero_row_mean)

    assert true_nonzero_row_means == nonzero_row_means

#test that rowzero gets correct nonzero row means with an all zero row
def test_stats_rowzero_all_zeros(fake_count_rowzero_obj):
    output = RowZero(fake_count_rowzero_obj)
    zeros = output['zeros']

    true_nonzero_row_means = [5, 6, 0]
    nonzero_row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        nonzero_row_mean = row.get('nonzero_mean')
        nonzero_row_means.append(nonzero_row_mean)

    assert true_nonzero_row_means == nonzero_row_means

#test that json output for rowzero function is correct
def test_stats_rowzero_json(fake_count_rowzero_obj):

    output = RowZero(fake_count_rowzero_obj)

    json_output = output.json

    name = json_output.get('name')
    zeros = json_output.get('properties', {}).get('zeros')

    true_row_names = ['gene1', 'gene2', 'gene3']

    row_names = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        row_name = row.get('name')
        row_names.append(row_name)
    
    true_zero_counts = [0, 0, 5]

    zero_counts = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        zero_count = row.get('zero_count')
        zero_counts.append(zero_count)
    
    true_zero_fracs = [0, 0, 1]

    zero_fracs = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        zero_frac = row.get('zero_frac')
        zero_fracs.append(zero_frac)

    true_row_means = [5, 6, 0]
    
    row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        row_mean = row.get('mean')
        row_means.append(row_mean)

    true_nonzero_row_means = [5, 6, 0]

    nonzero_row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        nonzero_row_mean = row.get('nonzero_mean')
        nonzero_row_means.append(nonzero_row_mean)

    assert name=='rowzero'
    assert true_row_names==row_names
    assert true_zero_counts==zero_counts
    assert true_zero_fracs == zero_fracs
    assert true_row_means==row_means
    assert true_nonzero_row_means==nonzero_row_means

def test_stats_rowzero_output(fake_counts_obj_with_zeros):
    output = RowZero(fake_counts_obj_with_zeros)
    assert output.output[0] == [
            'name','zero_count','zero_frac',
            'mean','median','nonzero_mean','nonzero_median'
        ]
    assert output.output[1] == ['gene1', 1, 1/3, 2, 2, 3, 3]
    assert output.output[2][:2] == ['gene2', 2]
    assert output.output[3][:2] == ['gene3', 2]
    assert output.output[4][:2] == ['gene4', 1]
    assert output.output[5][:2] == ['gene5', 0]

################################################################################
# entropy tests
#test that entropy function gets correct row names
def test_stats_entropy_names(fake_counts_obj):
    output = Entropy(fake_counts_obj)
    entropies = output['entropies']

    true_row_names = ['gene1', 'gene2', 'gene3', 'gene4', 'gene5']

    row_names = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_name = row.get('name')
        row_names.append(row_name)

    assert true_row_names == row_names

#test that entropy function calculates correct entropy values
def test_stats_entropies(fake_counts_obj):
    from math import log
    output = Entropy(fake_counts_obj)
    entropies = output['entropies']

    true_entropies = [
            -(2/14*log(2/14)+4/14*log(4/14)+8/14*log(8/14)),
            -(3/39*log(3/39)+9/39*log(9/39)+27/39*log(27/39)),
            -(4/84*log(4/84)+16/84*log(16/84)+64/84*log(64/84)),
            -(5/155*log(5/155)+25/155*log(25/155)+125/155*log(125/155)),
            -(6/258*log(6/258)+36/258*log(36/258)+216/258*log(216/258))
        ]

    row_entropies = []
    for i in range(len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert true_entropies == row_entropies

#test that entropy function calculates correct entropy values when there are 0 counts
def test_stats_entropies_with_zeros(fake_counts_obj_with_zeros):
    from math import log
    output = Entropy(fake_counts_obj_with_zeros)
    entropies = output['entropies']

    true_entropies = [
        -(2/6*log(1/3)+4/6*log(4/6)),
        0,
        0,
        -(5/130*log(5/130)+125/130*log(125/130)),
        -(6/258*log(6/258)+36/258*log(36/258)+216/258*log(216/258))
    ]

    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert true_entropies == row_entropies

#test that entropy gets correct values with an all zero row
def test_stats_entropy_all_zeros(fake_count_rowzero_obj):
    from math import log
    output = Entropy(fake_count_rowzero_obj)
    entropies = output['entropies']

    H1 = -((1/25)*log(1/25) + (3/25)*log(3/25) + (5/25)*log(5/25)
               + (7/25)*log(7/25) + (9/25)*log(9/25))
    H2 = -((2/30)*log(2/30) + (4/30)*log(4/30) + (6/30)*log(6/30)
               + (8/30)*log(8/30) + (10/30)*log(10/30))
    H3 = 0
    true_entropies = [H1, H2, H3]
    
    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert true_entropies == row_entropies

#test that json output for entropy function is correct
def test_stats_entropy_json(fake_count_rowzero_obj):

    output = Entropy(fake_count_rowzero_obj)
    entropies = output['entropies']
    json_output = output.json

    true_row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        true_row_entropy = row.get('entropy')
        true_row_entropies.append(true_row_entropy)

    name = json_output.get('name')
    entropies = json_output.get('properties', {}).get('entropies')

    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert name=='entropy'
    assert true_row_entropies==row_entropies

def test_stats_entropy_output(fake_count_rowzero_obj):
    from math import log
    output = Entropy(fake_count_rowzero_obj)

    H1 = -((1/25)*log(1/25) + (3/25)*log(3/25) + (5/25)*log(5/25)
               + (7/25)*log(7/25) + (9/25)*log(9/25))
    H2 = -((2/30)*log(2/30) + (4/30)*log(4/30) + (6/30)*log(6/30)
               + (8/30)*log(8/30) + (10/30)*log(10/30))
    H3 = 0

    assert output.output[0] == ['name','entropy']
    assert output.output[1:] == [['gene1',H1],['gene2',H2],['gene3',H3]]
 
################################################################################
# PCA tests
@pytest.fixture
def pca_counts_obj(request) :

    np.random.seed(1337)

    # first principal component should be about (9.5, -9.5) or so
    X = np.array([[_,_] for _ in range(10,100)]).astype(float)
    # add a little noise to avoid invalid component variance
    X += 0.01*np.random.random(size=X.shape)

    return CountMatrix(
            pandas.DataFrame(
                X,
                columns=('a','b'),
                index=['gene{}'.format(_) for _ in range(X.shape[0])]
            )
        )

def test_stats_countPCA(pca_counts_obj):

    output = CountPCA(pca_counts_obj)
    assert output.name == 'pca'

def test_stats_PCA_col_names(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    col_names = output['column_names']
    true_col_names = ['a', 'b']
    assert col_names == true_col_names

def test_stats_PCA_num_components(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    num_components = len(output['components'])
    assert num_components == 2

def test_stats_PCA_component_names(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_comp_names = ['PC1', 'PC2']
    comp_names = []
    components = output['components']
    for item in components:
        comp_names.append(item.get('name'))
    assert true_comp_names == comp_names

def test_stats_PCA_num_scores(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_num_scores = [min(*pca_counts_obj.counts.shape)]*2
    num_scores = []
    components = output['components']
    for item in components:
        num_scores.append(len(item.get('scores')))
    assert true_num_scores == num_scores

def test_stats_PCA_num_projections(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_num_projections = [2, 2]
    num_projections = []
    components = output['components']
    for item in components:
        num_projections.append(len(item.get('projections')))
    assert true_num_projections == num_projections

def test_stats_PCA_perc_variance(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_perc_variance = [1, 0.]
    perc_variance = []
    components = output['components']
    for item in components:
        perc_variance.append(item.get('perc_variance'))
    assert np.allclose(true_perc_variance, perc_variance,atol=0.1)

def test_stats_PCA_scores(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_scores = [[9.48,-9.48],[0,0]]
    scores = []
    components = output['components']
    for item in components:
        scores.append(item.get('scores'))
    assert np.allclose(true_scores, scores, atol=0.1)

def test_stats_PCA_projections(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_projections = np.array([[0.1,0.99],[0.1,0]])
    projections = []
    components = output['components']
    for item in components:
        projections.append([abs(_) for _ in item.get('projections')])
    assert np.allclose(true_projections, projections, atol=0.1)

def test_stats_PCA_json(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_projections = np.array([[0.1,0.99],[0.1,0]])
    projections = []
    output = output.json
    components = output['properties']['components']
    for item in components:
        projections.append([abs(_) for _ in item.get('projections')])
    assert np.allclose(true_projections, projections, atol=0.1)

def test_stats_PCA_output(pca_counts_obj):
    output = CountPCA(pca_counts_obj)
    true_projections = np.array([[0.1,0.99],[0.1,0]])
    assert output.output[0] == ('colname','PC1_100','PC2_000')
    a_proj, pc1, pc2 = output.output[1]
    assert a_proj == 'a'
    assert np.isclose(abs(pc1),0.1,atol=0.1)
    assert np.isclose(abs(pc2),0.1,atol=0.1)

    b_proj, pc1, pc2 = output.output[2]
    assert b_proj == 'b'
    assert np.isclose(abs(pc1),0.99,atol=0.1)
    assert np.isclose(abs(pc2),0.0,atol=0.1)

################################################################################
# summary tests
#test that all functions were written to json output when summary is called
def test_stats_summary_json(fake_counts_obj):

    output = summary(fake_counts_obj)

    true_funcs = set(['basestats', 'coldist', 'colzero', 'rowzero', 'entropy', 'pca'])

    names = set()
    for section in output :
        names.add(section.json['name'])

    assert true_funcs==names

#test that all functions were written to json output when summary is called
def test_stats_cli_json(fake_count_rowdist_obj, fake_count_rowdist_csv):

    output = summary(fake_count_rowdist_obj)

    true_funcs = set(['basestats', 'coldist', 'colzero', 'rowzero', 'entropy','pca'])

    with tempfile.TemporaryDirectory() as d :

        main(['detk-stats','summary','--report-dir={}'.format(d),
            '-o','/dev/null',fake_count_rowdist_csv])

        # check that there is that number of output json files
        json_fns = os.listdir(os.path.join(d,'json'))
        assert len(json_fns) == len(true_funcs)

        names = set()
        for fn in json_fns :
            with open(os.path.join(d,'json',fn)) as f :
                names.add(json.load(f)['name'])

        assert true_funcs==names


