import numpy as np
import os
import pandas
import pytest
import tempfile
import json
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
          print(['detk-stats',cmd,f'--report-dir={d}',fake_counts_csv])
          main(['detk-stats',cmd,f'--report-dir={d}',fake_counts_csv])

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
      data.append([f'gene{i}']+[i]*3)
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
    assert not output.params['log']
    assert not output.params['density']

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
    coldist_true = 10**np.percentile(
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
    assert np.allclose(col_dist_bins,10**true_bins[:-1])

    col_dist_func = [[_[1] for _ in d['dist']] for d in col_dists]
    true_dists = [[13,100-13]]*3
    assert col_dist_func==true_dists

#test that json output for coldist function is correct
def test_stats_coldist_json(fake_count_coldist_obj):
    output = ColDist(fake_count_coldist_obj, bins=10)

    json_output = output.json

    name = json_output.get('name')
    dists = json_output.get('properties', {}).get('dists')

    [10*x for x in range(1, 11)]

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
            colnames.append(f'{col}__{colstat}')
    assert output.output[0] == colnames

################################################################################
# rowdist tests
@pytest.fixture
def fake_count_list_data_rowdist() :
  data = [['gene']+[f's{_}' for _ in range(100)]]
  for i in range(3) :
      data.append([f'gene{i+1}']+[_+1 for _ in range(100)])
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
    assert not output.params['log']
    assert not output.params['density']

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
def test_stats_rowdist_log(fake_count_rowdist_obj):
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
def fake_counts_list_data_rowzero() :
  data = [
  [ 'gene', 'a', 'b', 'c', 'd', 'e'],
  [ 'gene1', 1, 1, 1, 1, 1],
  [ 'gene2', 1, 1, 1, 1, 0],
  [ 'gene3', 1, 1, 1, 0, 0],
  [ 'gene4', 1, 1, 0, 0, 0],
  [ 'gene5', 1, 0, 0, 0, 0],
  [ 'gene6', 0, 0, 0, 0, 0]
  ]
  return data


#convert to csv from 2-D list
@pytest.fixture
def fake_counts_rowzero_csv(request,fake_counts_list_data_rowzero) :
  with pytest.temp_csv_wrap(fake_counts_list_data_rowzero,',') as f :
    yield f.name

@pytest.fixture
def fake_counts_rowzero_obj(
  fake_counts_rowzero_csv
  ,fake_column_data_csv
  ,fake_design) :

  return pytest.make_counts_obj(
    fake_counts_rowzero_csv
    ,fake_column_data_csv
    ,fake_design
  )

#test that rowzero function gets correct row names
def test_stats_rowzero_numzero(fake_counts_rowzero_obj):
    from collections import defaultdict
    output = RowZero(fake_counts_rowzero_obj)
    zeros = output['zeros']

    stats = defaultdict(list)
    for i in range(0, len(zeros)):
        for k,v in zeros[i].items() :
            stats[k].append(v)

    assert stats['num_zeros'] == [0,1,2,3,4,5]
    assert stats['num_features'] == [1]*6
    assert np.allclose(stats['feature_frac'], [1/6]*6)
    assert np.allclose(stats['cum_feature_frac'], [(_+1)/6 for _ in range(6)])
    assert stats['mean'] == [1,.8,.6,.4,.2,0]
    assert stats['nonzero_mean'] == [1]*5+[0]
    assert stats['median'] == [1,1,1,0,0,0]
    assert stats['nonzero_median'] == [1,1,1,1,1,0]

#test that json output for rowzero function is correct
def test_stats_rowzero_json(fake_counts_rowzero_obj):

    from collections import defaultdict
    output = RowZero(fake_counts_rowzero_obj)

    zeros = output.json['properties']['zeros']

    stats = defaultdict(list)
    for i in range(0, len(zeros)):
        for k,v in zeros[i].items() :
            stats[k].append(v)

    assert stats['num_zeros'] == [0,1,2,3,4,5]
    assert stats['num_features'] == [1]*6
    assert np.allclose(stats['feature_frac'], [1/6]*6)
    assert np.allclose(stats['cum_feature_frac'], [(_+1)/6 for _ in range(6)])
    assert stats['mean'] == [1,.8,.6,.4,.2,0]
    assert stats['nonzero_mean'] == [1]*5+[0]
    assert stats['median'] == [1,1,1,0,0,0]
    assert stats['nonzero_median'] == [1,1,1,1,1,0]


def test_stats_rowzero_output(fake_counts_rowzero_obj):
    output = RowZero(fake_counts_rowzero_obj)
    assert output.output[0] == [
            'num_zeros','num_features','feature_frac','cum_feature_frac',
            'mean','nonzero_mean','median','nonzero_median'
        ]
    assert output.output[1] == [0, 1, 1/6, 1/6, 1, 1, 1, 1]
    assert output.output[2][:2] == [1, 1]
    assert output.output[3][:2] == [2, 1]
    assert output.output[4][:2] == [3, 1]
    assert output.output[5][:2] == [4, 1]
    assert output.output[6][:2] == [5, 1]

################################################################################
# entropy tests
@pytest.fixture
def fake_counts_list_data_entropy() :
    # this counts matrix is a 100x99 lower diagonal of 1s
    data = [['gene']+[f's{_+1}' for _ in range(99)]]
    for i in range(100) :
        data.append([f'gene{i+1}']+[1]*i+[0]*(99-i))
    return data

#convert to csv from 2-D list
@pytest.fixture
def fake_counts_entropy_csv(request,fake_counts_list_data_entropy) :
    with pytest.temp_csv_wrap(fake_counts_list_data_entropy,',') as f :
        yield f.name

@pytest.fixture
def fake_counts_entropy_obj(fake_counts_entropy_csv) :

    return pytest.make_counts_obj(fake_counts_entropy_csv,None,None)

#test that entropy function calculates correct entropy values
def test_stats_entropies(fake_counts_entropy_obj):
    output = Entropy(fake_counts_entropy_obj)
    entropies = output['entropies']

    true_pct = list(range(100))
    assert np.allclose(entropies['pct'],true_pct)

    true_entropies = [0]+[-i*(1/i)*np.log(1/i) for i in range(1,100)]
    #assert np.allclose(entropies['entropies'],true_entropies)

    np.percentile(true_entropies,true_pct,method='higher')

    assert np.allclose(
        entropies['pctVal'],
        np.percentile(true_entropies,true_pct,method='higher')
    )
    assert np.allclose(entropies['num_features'], [0,2]+[1]*98)
    assert np.allclose(entropies['frac_features'], [0,2/100]+[1/100]*98)
    assert np.allclose(entropies['cum_frac_features'], [0]+[i/100 for i in range(2,101)])
    assert entropies['exemplar_features'][1]['name'] == 'gene1'
    assert entropies['exemplar_features'][1]['entropy'] == 0
    assert entropies['exemplar_features'][1]['counts'][0] == ('s1',0)

#test that json output for entropy function is correct
def test_stats_entropy_json(fake_counts_entropy_obj):

    output = Entropy(fake_counts_entropy_obj)
    entropies = output.json['properties']['entropies']

    true_pct = list(range(100))
    assert np.allclose(entropies['pct'],true_pct)

    true_entropies = [0]+[-i*(1/i)*np.log(1/i) for i in range(1,100)]
    #assert np.allclose(entropies['entropies'],true_entropies)

    np.percentile(true_entropies,true_pct,method='higher')

    assert np.allclose(
        entropies['pctVal'],
        np.percentile(true_entropies,true_pct,method='higher')
    )
    assert np.allclose(entropies['num_features'], [0,2]+[1]*98)
    assert np.allclose(entropies['frac_features'], [0,2/100]+[1/100]*98)
    assert np.allclose(entropies['cum_frac_features'], [0]+[i/100 for i in range(2,101)])
    assert entropies['exemplar_features'][1]['name'] == 'gene1'
    assert entropies['exemplar_features'][1]['entropy'] == 0
    assert entropies['exemplar_features'][1]['counts'][0] == ('s1',0)

def test_stats_entropy_output(fake_counts_entropy_obj):
    output = Entropy(fake_counts_entropy_obj)
    [0]+[-i*(1/i)*np.log(1/i) for i in range(1,101)]
    output = output.output

    assert output[0][:4] == ['pct','pctVal','num_features','frac_features']
    assert output[1][:4] == (0, 0, 0, 0)
    assert output[2][:4] == (1, 0, 2, 2/100)
 
################################################################################
# PCA tests
@pytest.fixture
def pca_counts_obj(request) :

    np.random.seed(1337)

    # first principal component should be about (9.5, -9.5) or so
    X = np.array([[_,_] for _ in range(10,100)]).astype(float)
    # add a little noise to avoid invalid component variance
    X += 0.01*np.random.random(size=X.shape)

    counts = pandas.DataFrame(
                X,
                columns=('a','b'),
                index=[f'gene{_}' for _ in range(X.shape[0])]
            )
    col_data = pandas.DataFrame({
        'cond': ['c1','c2'],
        'cov': [0,1]
        },
        index=counts.columns
    )

    return CountMatrix(
            counts,
            col_data
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
    # PCA component signs are arbitrary (eigenvector orientation is not
    # determined and varies by sklearn/LAPACK version), so compare magnitudes
    assert np.allclose(np.abs(true_scores), np.abs(scores), atol=0.1)

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
    np.array([[0.1,0.99],[0.1,0]])
    assert output.output[0] == ('colname','PC1_100','PC2_000')
    a_proj, pc1, pc2 = output.output[1]
    assert a_proj == 'a'
    assert np.isclose(abs(pc1),0.1,atol=0.1)
    assert np.isclose(abs(pc2),0.1,atol=0.1)

    b_proj, pc1, pc2 = output.output[2]
    assert b_proj == 'b'
    assert np.isclose(abs(pc1),0.99,atol=0.1)
    assert np.isclose(abs(pc2),0.0,atol=0.1)

def test_stats_PCA_coldata(pca_counts_obj) :

    output = CountPCA(pca_counts_obj)

    colvar = output.json['properties']['column_variables']
    assert colvar['sample_names'] == ['a','b']
    assert len(colvar['columns']) == 2
    assert colvar['columns'][0]['column'] == 'cond'
    assert colvar['columns'][0]['values'] == ['c1','c2']

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
def test_stats_summary_sparse_json():

    with tempfile.TemporaryDirectory() as d :

        main(['detk-stats','summary',f'--report-dir={d}',
            '-o','/dev/null','tests/stats/sparse_counts.csv'])

#test that all functions were written to json output when summary is called
def test_stats_cli_json(fake_count_rowdist_obj, fake_count_rowdist_csv):

    summary(fake_count_rowdist_obj)

    true_funcs = set(['basestats', 'coldist', 'colzero', 'rowzero', 'entropy','pca'])

    with tempfile.TemporaryDirectory() as d :

        main(['detk-stats','summary',f'--report-dir={d}',
            '-o','/dev/null',fake_count_rowdist_csv])

        # check that there is that number of output json files
        json_fns = os.listdir(os.path.join(d,'json'))
        assert len(json_fns) == len(true_funcs)

        names = set()
        for fn in json_fns :
            with open(os.path.join(d,'json',fn)) as f :
                names.add(json.load(f)['name'])

        assert true_funcs==names

