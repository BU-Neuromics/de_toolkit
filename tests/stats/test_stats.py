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

def test_stats_cli() :
  from de_toolkit.stats import main
  from docopt import DocoptExit
  for cmd in ('summary','base','coldist','rowdist','colzero','rowzero','entropy','pca') :
      with pytest.raises(DocoptExit) :
          main(['detk-stats',cmd])

# write and remove a json file containing the given output
def get_json_output(output) :
    with tempfile.NamedTemporaryFile() as f :
        json_fn = f.name

    #Format JSON output file
    if not isinstance(output,list) :
        output = [output]

    format_json(json_fn, output)

    with open(json_fn) as f :
        json_output = json.load(f)

    os.remove(json_fn)

    return json_output

#test that all functions were written to JSON output when summary is called
def test_stats_cli_JSON(fake_count_rowdist_obj, fake_count_rowdist_csv):

    output = summary(fake_count_rowdist_obj)

    true_funcs = set(['base', 'coldist', 'rowdist', 'colzero', 'rowzero', 'entropy'])

    with tempfile.NamedTemporaryFile() as f :
        json_fn = f.name

    main(['detk-stats','summary','--json={}'.format(json_fn),fake_count_rowdist_csv])
    with open(json_fn) as f :
        output = json.load(f)

    names = set()
    for section in output :
        names.add(section['name'])

    os.remove(json_fn)

    assert true_funcs==names

################################################################################
# base tests
#test for base function
def test_stats_base(fake_counts_obj):
    output = base(fake_counts_obj)
    cols = output.get('stats', {}).get('num_cols')
    rows = output.get('stats', {}).get('num_rows')
    n = output.get('name')
    assert cols==3
    assert rows==5
    assert n=='base'

#test that JSON output for base function is correct
def test_stats_base_JSON(fake_counts_obj):
    output = base(fake_counts_obj)

    json_output = get_json_output(output)[0]

    name = json_output.get('name')
    cols = json_output.get('stats', {}).get('num_cols')
    rows = json_output.get('stats', {}).get('num_rows')

    assert name=='base'
    assert cols==3
    assert rows==5


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
def test_stats_coldist_names(fake_count_coldist_obj):
    output = coldist(fake_count_coldist_obj, 20, -1, -1)
    col_dists = output.get('stats').get('dists')
    col_name_func = [d['name'] for d in col_dists]

    col_name_true = ['a','b','c']
    assert col_name_func == col_name_true

#test that coldist function gets correct column dist
def test_stats_coldist_dist(fake_count_coldist_obj):
    output = coldist(fake_count_coldist_obj, bins=10)
    col_dists = output.get('stats').get('dists')
    col_dist_func = [d['dist'] for d in col_dists]
    col_dist_true = [[10.0 for i in range(10)] for j in range(3)]
    assert col_dist_func == col_dist_true

#test that coldist function with density option gets correct dists
def test_stats_coldist_density(fake_count_coldist_obj):
    output = coldist(fake_count_coldist_obj, 20, density=True)
    col_dists = output.get('stats').get('dists')
    col_dist_func = [d['dist'] for d in col_dists]
    col_dist_sums = [sum(x) for x in col_dist_func]
    
    col_dist_true = [1.0 for i in range(3)]

    assert np.allclose(col_dist_sums,col_dist_true)

#test that coldist function get correct number of bins
def test_stats_coldist_bins(fake_count_coldist_obj):
    output = coldist(fake_count_coldist_obj, bins=5)
    col_dists = output.get('stats').get('dists')
    col_dist_bins = [d['bins'] for d in col_dists]
    num_bins = [len(b) for b in col_dist_bins]
    true_bins = [5, 5, 5]

    assert num_bins == true_bins

#test log option for coldist function
def test_stats_coldist_log_bins():
    f = open('tests/stats/test_coldist.csv', 'r')
    count_obj = CountMatrixFile(f)
    output = coldist(count_obj, bins=2, log=True)
    col_dists = output.get('stats').get('dists')
    col_dist_bins = [d['bins'] for d in col_dists]
    col_dist_func = [d['dist'] for d in col_dists]
    true_bins = [[1.5, 2.0],[3.5, 4.0], [5.5, 6.0]]
    true_dists = [[2,2],[2,2],[2,2]]
    assert col_dist_bins==true_bins
    assert col_dist_func==true_dists

#test that JSON output for coldist function is correct
def test_stats_coldist_JSON(fake_count_coldist_obj):
    output = coldist(fake_count_coldist_obj, bins=10)

    json_output = get_json_output(output)[0]

    name = json_output.get('name')
    pct = json_output.get('stats', {}).get('pct')
    dists = json_output.get('stats', {}).get('dists')    

    true_pct = [x for x in range(5, 100, 5)]

    true_col_names = ['a', 'b', 'c']
    col_names = []
    for i in range(0, len(dists)):
        dist = dists[i]
        col_name = dist['name']
        col_names.append(col_name)

    col_dists = json_output.get('stats').get('dists')
    col_dist_func = [d['dist'] for d in col_dists]
    col_dist_true = [[10.0 for i in range(10)] for j in range(3)]

    assert name=='coldist'
    assert pct==true_pct
    assert true_col_names==col_names
    assert col_dist_func==col_dist_true


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

#test that rowdist function gets correct row names
def test_stats_rowdist_names(fake_count_rowdist_obj):
    output = rowdist(fake_count_rowdist_obj, 20, -1, -1)
    row_dists = output.get('stats').get('dists')
    row_name_func = [d['name'] for d in row_dists]

    row_name_true = ['gene1','gene2','gene3']
    assert row_name_func == row_name_true

#test that rowdist function gets correct row dists
def test_stats_rowdist_dist(fake_count_rowdist_obj):
    output = rowdist(fake_count_rowdist_obj, bins=10)
    row_dists = output.get('stats').get('dists')
    row_dist_func = [d['dist'] for d in row_dists]
    row_dist_true = [[10.0 for i in range(10)] for j in range(3)]
    assert row_dist_func == row_dist_true


#test that rowdist function with density option gets correct dists
def test_stats_rowdist_density(fake_count_rowdist_obj):
    output = rowdist(fake_count_rowdist_obj, 20, -1, 1)
    row_dists = output.get('stats').get('dists')
    row_dist_func = [d['dist'] for d in row_dists]
    row_dist_sums = [sum(x) for x in row_dist_func]
    
    row_dist_true = [1.0 for i in range(3)]

    assert np.allclose(row_dist_sums,row_dist_true)

#test that rowdist function get correct number of bins
def test_stats_rowdist_bins(fake_count_rowdist_obj):
    output = rowdist(fake_count_rowdist_obj, 5, -1, -1)
    row_dists = output.get('stats').get('dists')
    row_dist_bins = [d['bins'] for d in row_dists]
    num_bins = [len(b) for b in row_dist_bins]
    true_bins = [5, 5, 5]

    assert num_bins == true_bins
    
#test log option for rowdist function
def test_stats_rowdist_bins(fake_count_rowdist_obj):
    output = rowdist(fake_count_rowdist_obj, bins=2, log=True)
    row_dists = output.get('stats').get('dists')
    row_dist_bins = [d['bins'] for d in row_dists]
    row_dist_func = [d['dist'] for d in row_dists]
    true_bins = [[1,2]]*3
    true_dists = [[9,91]]*3
    assert row_dist_bins==true_bins
    assert row_dist_func==true_dists

#test that JSON output for rowdist function is correct
def test_stats_rowdist_JSON(fake_count_rowdist_obj):

    output = rowdist(fake_count_rowdist_obj, bins=2, log=True)

    json_output = get_json_output(output)[0]

    name = json_output.get('name')
    pct = json_output.get('stats', {}).get('pct')
    dists = json_output.get('stats', {}).get('dists')    

    true_pct = [x for x in range(5, 100, 5)]

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


################################################################################
# colzero tests
#test that colzero function gets correct column names
def test_stats_colzero_names(fake_counts_obj_with_zeros):
    output = colzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_col_names = ['a', 'b', 'c']

    col_names = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        name = col.get('name')
        col_names.append(name)

    assert true_col_names==col_names

#test that colzero function gets correct zero counts
def test_stats_colzero_zero_counts(fake_counts_obj_with_zeros):
    output = colzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_zero_counts = [1, 2, 3]

    zero_counts = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        zero_count = col.get('zero_count')
        zero_counts.append(zero_count)

    assert true_zero_counts==zero_counts

#test that colzero function gets correct zero fractions
def test_stats_colzero_zero_fracs(fake_counts_obj_with_zeros):
    output = colzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_zero_fracs = [1/5, 2/5, 3/5]

    zero_fracs = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        zero_frac = col.get('zero_frac')
        zero_fracs.append(zero_frac)

    assert true_zero_fracs == zero_fracs

#test that colzero function gets correct column means
def test_stats_colzero_col_means(fake_counts_obj_with_zeros):
    output = colzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_col_means = [(2+4+5+6)/5, (4+9+36)/5, (125+216)/5]

    col_means = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        col_mean = col.get('mean')
        col_means.append(col_mean)

    assert true_col_means == col_means

#test that colzero function gets correct nonzero column means
def test_stats_colzero_nonzero_col_means(fake_counts_obj_with_zeros):
    output = colzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_nonzero_col_means = [(2+4+5+6)/4, (4+9+36)/3, (125+216)/2]

    nonzero_col_means = []
    for i in range(0, len(zeros)):
        col = zeros[i]
        nonzero_col_mean = col.get('nonzero_mean')
        nonzero_col_means.append(nonzero_col_mean)

    assert true_nonzero_col_means == nonzero_col_means

#test that JSON output for colzero function is correct
def test_stats_colzero_JSON(fake_counts_obj_with_zeros):

    output = colzero(fake_counts_obj_with_zeros)

    json_output = get_json_output(output)[0]
    name = json_output.get('name')
    zeros = json_output.get('stats', {}).get('zeros')

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
    output = rowzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_row_names = ['gene1', 'gene2', 'gene3', 'gene4', 'gene5']

    row_names = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        row_name = row.get('name')
        row_names.append(row_name)

    assert true_row_names == row_names

#test that rowzero function gets correct zero counts
def test_stats_rowzero_zero_counts(fake_counts_obj_with_zeros):
    output = rowzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_zero_counts = [1, 2, 2, 1, 0]

    zero_counts = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        zero_count = row.get('zero_count')
        zero_counts.append(zero_count)

    assert true_zero_counts == zero_counts

#test that rowzero function gets correct zero fractions
def test_stats_rowzero_zero_fracs(fake_counts_obj_with_zeros):
    output = rowzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_zero_fracs = [1/3, 2/3, 2/3, 1/3, 0]

    zero_fracs = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        zero_frac = row.get('zero_frac')
        zero_fracs.append(zero_frac)

    assert true_zero_fracs == zero_fracs

#test that rowzero function gets correct row means
def test_stats_rowzero_row_means(fake_counts_obj_with_zeros):
    output = rowzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_row_means = [(2+4)/3, 9/3, 4/3, (5+125)/3, (6+36+216)/3]

    row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        row_mean = row.get('mean')
        row_means.append(row_mean)

    assert true_row_means == row_means

#test that rowzero function gets correct nonzero row means
def test_stats_rowzero_row_means(fake_counts_obj_with_zeros):
    output = rowzero(fake_counts_obj_with_zeros)
    zeros = output.get('stats', {}).get('zeros')

    true_nonzero_row_means = [(2+4)/2, 9, 4, (5+125)/2, (6+36+216)/3]

    nonzero_row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        nonzero_row_mean = row.get('nonzero_mean')
        nonzero_row_means.append(nonzero_row_mean)

    assert true_nonzero_row_means == nonzero_row_means

#test that rowzero gets correct nonzero row means with an all zero row
def test_stats_rowzero_all_zeros(fake_count_rowzero_obj):
    output = rowzero(fake_count_rowzero_obj)
    zeros = output.get('stats', {}).get('zeros')

    true_nonzero_row_means = [5, 6, 0]
    nonzero_row_means = []
    for i in range(0, len(zeros)):
        row = zeros[i]
        nonzero_row_mean = row.get('nonzero_mean')
        nonzero_row_means.append(nonzero_row_mean)

    assert true_nonzero_row_means == nonzero_row_means

#test that JSON output for rowzero function is correct
def test_stats_rowzero_JSON(fake_count_rowzero_obj):

    output = rowzero(fake_count_rowzero_obj)

    json_output = get_json_output(output)[0]

    name = json_output.get('name')
    zeros = json_output.get('stats', {}).get('zeros')

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


################################################################################
# entropy tests
#test that entropy function gets correct row names
def test_stats_entropy_names(fake_counts_obj):
    output = entropy(fake_counts_obj)
    entropies = output.get('stats', {}).get('entropies')

    true_row_names = ['gene1', 'gene2', 'gene3', 'gene4', 'gene5']

    row_names = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_name = row.get('name')
        row_names.append(row_name)

    assert true_row_names == row_names

#test that entropy function calculates correct entropy values
def test_stats_entropies(fake_counts_obj):
    output = entropy(fake_counts_obj)
    entropies = output.get('stats', {}).get('entropies')

    H1 = -((2/14)*math.log(2/14,2) + (4/14)*math.log(4/14,2) + (8/14)*math.log(8/14,2))
    H2 = -((3/39)*math.log(3/39,2) + (9/39)*math.log(9/39,2) + (27/39)*math.log(27/39,2))
    H3 = -((4/84)*math.log(4/84,2) + (16/84)*math.log(16/84,2) + (64/84)*math.log(64/84,2))
    H4 = -((5/155)*math.log(5/155,2) + (25/155)*math.log(25/155,2) + (125/155)*math.log(125/155,2))
    H5 = -((6/258)*math.log(6/258,2) + (36/258)*math.log(36/258,2) + (216/258)*math.log(216/258,2))
    true_entropies = [H1, H2, H3, H4, H5]

    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert true_entropies == row_entropies

#test that entropy function calculates correct entropy values when there are 0 counts
def test_stats_entropies(fake_counts_obj_with_zeros):
    output = entropy(fake_counts_obj_with_zeros)
    entropies = output.get('stats', {}).get('entropies')

    H1 = -((2/6)*math.log(2/6,2) + (4/6)*math.log(4/6,2))
    H2 = -((9/9)*math.log(9/9,2))
    H3 = -((4/4)*math.log(4/4,2))
    H4 = -((5/130)*math.log(5/130,2) + (125/130)*math.log(125/130,2))
    H5 = -((6/258)*math.log(6/258,2) + (36/258)*math.log(36/258,2) + (216/258)*math.log(216/258,2))
    true_entropies = [H1, H2, H3, H4, H5]

    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)


    assert true_entropies == row_entropies

#test that entropy gets correct values with an all zero row
def test_stats_entropy_all_zeros(fake_count_rowzero_obj):
    output = entropy(fake_count_rowzero_obj)
    entropies = output.get('stats', {}).get('entropies')

    H1 = -((1/25)*math.log(1/25,2) + (3/25)*math.log(3/25,2) + (5/25)*math.log(5/25,2)
               + (7/25)*math.log(7/25,2) + (9/25)*math.log(9/25,2))
    H2 = -((2/30)*math.log(2/30,2) + (4/30)*math.log(4/30,2) + (6/30)*math.log(6/30,2)
               + (8/30)*math.log(8/30,2) + (10/30)*math.log(10/30,2))
    H3 = 0
    true_entropies = [H1, H2, H3]
    
    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert true_entropies == row_entropies

#test that JSON output for entropy function is correct
def test_stats_entropy_JSON(fake_count_rowzero_obj):

    output = entropy(fake_count_rowzero_obj)
    entropies = output['stats']['entropies']
    json_output = get_json_output(output)[0]

    true_row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        true_row_entropy = row.get('entropy')
        true_row_entropies.append(true_row_entropy)

    name = json_output.get('name')
    entropies = json_output.get('stats', {}).get('entropies')

    row_entropies = []
    for i in range(0, len(entropies)):
        row = entropies[i]
        row_entropy = row.get('entropy')
        row_entropies.append(row_entropy)

    assert name=='entropy'
    assert true_row_entropies==row_entropies

#test that all functions were written to JSON output when summary is called
def test_stats_summary_JSON(fake_count_rowdist_obj, fake_count_rowdist_csv):

    output = summary(fake_count_rowdist_obj)

    json_output = get_json_output(output)

    true_funcs = set(['base', 'coldist', 'rowdist', 'colzero', 'rowzero', 'entropy'])

    names = set()
    for section in json_output :
        names.add(section['name'])

    assert true_funcs==names

@pytest.mark.skip(reason='will integrate PCA tests after merge')
def test_stats_countPCA(fake_counts_obj):

    output = count_PCA(fake_counts_obj)
    name = output.get('name')
    assert name == 'pca'

def test_stats_PCA_col_names(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    col_names = output.get('stats', {}).get('column_names')
    true_col_names = ['a', 'b', 'c']
    assert col_names == true_col_names

def test_stats_PCA_num_components(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    num_components = len(output.get('components'))
    assert num_components == 3

def test_stats_PCA_component_names(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    true_comp_names = ['PC1', 'PC2', 'PC3']
    comp_names = []
    components = output.get('components')
    for item in components:
      comp_names.append(item.get('name'))
    assert true_comp_names == comp_names

def test_stats_PCA_num_scores(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    true_num_scores = [5, 5, 5]
    num_scores = []
    components = output.get('components')
    for item in components:
      num_scores.append(len(item.get('scores')))
    assert true_num_scores == num_scores

def test_stats_PCA_num_projections(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    true_num_projections = [3, 3, 3]
    num_projections = []
    components = output.get('components')
    for item in components:
      num_projections.append(len(item.get('projections')))
    assert true_num_projections == num_projections

def test_stats_PCA_perc_variance(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    true_perc_variance = [0.9878246911444414, 0.01214185070132599, 3.34581542e-05]
    perc_variance = []
    components = output.get('components')
    for item in components:
      perc_variance.append(item.get('perc_variance'))
    assert np.allclose(true_perc_variance, perc_variance)

def test_stats_PCA_scores(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    true_scores = [[-2.13538377e+00, -1.32959347e+00, -2.84804960e-01, 1.04478851e+00, 2.70499369e+00],
                   [2.51638701e-01, -7.20344487e-02, -2.25158739e-01, -1.53124291e-01, 1.98678777e-01],
                   [-8.08657117e-03, 1.45810998e-02, 9.72247845e-04, -1.36088520e-02, 6.14207548e-03]]
    scores = []
    components = output.get('components')
    for item in components:
      scores.append(item.get('scores'))
    assert np.allclose(true_scores, scores)

def test_stats_PCA_projections(fake_counts_obj):
    output = count_PCA(fake_counts_obj)
    true_projections = [[0.57528892, -0.72606076, 0.37666754],
                [0.58086251, 0.03842312, -0.81309434],
            [0.57588315, 0.68655622, 0.44384587]]
    projections = []
    components = output.get('components')
    for item in components:
      projections.append(item.get('projections'))
    assert np.allclose(true_projections, projections)
