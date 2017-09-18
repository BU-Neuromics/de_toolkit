import docopt
import numpy as np
import os
import pandas
import pytest
import tempfile
import json
import math
from de_toolkit.common import *
from de_toolkit.stats import *

################################################################################
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
  with pytest.temp_csv_wrap(fake_count_list_data_coldist,',') as f :
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

  return pytest.make_counts_obj(
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
  with pytest.temp_csv_wrap(fake_count_list_data_rowdist,',') as f :
    yield f.name


@pytest.fixture
def fake_count_rowdist_obj(
  fake_count_rowdist_csv
  ,fake_column_data_csv
  ,fake_design) :

  return pytest.make_counts_obj(
    fake_count_rowdist_csv
    ,fake_column_data_csv
    ,fake_design
  )


################################################################################


#test for base function
def test_stats_base(fake_counts_obj):
	output = base(fake_counts_obj)
	cols = output.get('stats', {}).get('num_cols')
	rows = output.get('stats', {}).get('num_rows')
	n = output.get('name')
	assert cols==3 and rows==5 and n=='base'


#test that coldist function gets correct column names
def test_stats_coldist_names(fake_count_coldist_obj):
	output = coldist(fake_count_coldist_obj, 20, -1, -1)
	col_dists = output.get('stats').get('dists')
	col_name_func = [d['name'] for d in col_dists]
	print(col_name_func)

	col_name_true = ['a','b','c']
	assert col_name_func == col_name_true

#test that coldist function gets correct column dist
def test_stats_coldist_dist(fake_count_coldist_obj):
	output = coldist(fake_count_coldist_obj, 20, -1, -1)
	col_dists = output.get('stats').get('dists')
	col_dist_func = [d['dist'] for d in col_dists]

	col_dist_true = [[3.0 for i in range(20)] for j in range(3)]
	assert col_dist_func == col_dist_true

#test that coldist function with density option gets correct dists
def test_stats_coldist_density(fake_count_coldist_obj):
	output = coldist(fake_count_coldist_obj, 20, -1, 1)
	col_dists = output.get('stats').get('dists')
	col_dist_func = [d['dist'] for d in col_dists]
	col_dist_sums = [sum(x) for x in col_dist_func]
	
	col_dist_true = [1.0 for i in range(3)]

	assert np.allclose(col_dist_sums,col_dist_true)

#test that coldist function get correct number of bins
def test_stats_coldist_bins(fake_count_coldist_obj):
	output = coldist(fake_count_coldist_obj, 5, -1, -1)
	col_dists = output.get('stats').get('dists')
	col_dist_bins = [d['bins'] for d in col_dists]
	num_bins = [len(b) for b in col_dist_bins]
	true_bins = [5, 5, 5]

	assert num_bins == true_bins
	
#test log option for coldist function
def test_stats_coldist_bins():
	f = open('tests/stats/test_coldist.csv', 'r')
	count_obj = CountMatrixFile(f)
	output = coldist(count_obj, 2, 1, -1)
	col_dists = output.get('stats').get('dists')
	col_dist_bins = [d['bins'] for d in col_dists]	
	col_dist_func = [d['dist'] for d in col_dists]
	true_bins = [[1.5, 2.0],[3.5, 4.0], [5.5, 6.0]]
	true_dists = [[2,2],[2,2],[2,2]]
	assert col_dist_bins==true_bins and col_dist_func==true_dists

#test that rowdist function gets correct row names
def test_stats_rowdist_names(fake_count_rowdist_obj):
	output = rowdist(fake_count_rowdist_obj, 20, -1, -1)
	row_dists = output.get('stats').get('dists')
	row_name_func = [d['name'] for d in row_dists]

	row_name_true = ['gene1','gene2','gene3']
	assert row_name_func == row_name_true

#test that rowdist function gets correct row dists
def test_stats_rowdist_dist(fake_count_rowdist_obj):
	output = rowdist(fake_count_rowdist_obj, 20, -1, -1)
	row_dists = output.get('stats').get('dists')
	row_dist_func = [d['dist'] for d in row_dists]

	row_dist_true = [[1.0 for i in range(20)] for j in range(3)]
	assert row_dist_func == row_dist_true


#test that rowdist function with density option gets correct dists
def test_stats_coldist_density(fake_count_rowdist_obj):
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
def test_stats_rowdist_bins():
	f = open('tests/stats/test_rowdist.csv', 'r')
	count_obj = CountMatrixFile(f)
	output = rowdist(count_obj, 2, 1, -1)
	row_dists = output.get('stats').get('dists')
	row_dist_bins = [d['bins'] for d in row_dists]	
	row_dist_func = [d['dist'] for d in row_dists]
	true_bins = [[1.5, 2.0],[3.5, 4.0], [5.5, 6.0]]
	true_dists = [[2,2],[2,2],[2,2]]
	assert row_dist_bins==true_bins and row_dist_func==true_dists

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

#test that JSON output for base function is correct
def test_stats_base_JSON():
	test = open('tests/stats/fake_counts_base.json', 'r')
	for line in test:
		json_output = json.loads(line)
	
	name = json_output.get('name')
	cols = json_output.get('stats', {}).get('num_cols')
	rows = json_output.get('stats', {}).get('num_rows')
	
	assert name=='base' and cols==3 and rows==5

#test that JSON output for coldist function is correct
def test_stats_coldist_JSON():
	test = open('tests/stats/fake_counts_coldist.json', 'r')
	for line in test:
		json_output = json.loads(line)
	
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

	col_dist_func = [d['dist'] for d in dists]
	col_dist_true = [[3.0 for i in range(20)] for j in range(3)]

	assert name=='coldist' and pct==true_pct and true_col_names==col_names and col_dist_func==col_dist_true

#test that JSON output for rowdist function is correct
def test_stats_rowdist_JSON():
	test = open('tests/stats/fake_counts_rowdist.json', 'r')
	for line in test:
		json_output = json.loads(line)
	
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
	row_dist_true = [[1.0 for i in range(20)] for j in range(3)]

	assert name=='rowdist' and pct==true_pct and true_row_names==row_names and row_dist_func==row_dist_true

#test that JSON output for colzero function is correct
def test_stats_colzero_JSON():
	test = open('tests/stats/fake_counts_colzero.json', 'r')
	for line in test:
		json_output = json.loads(line)
	
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

	assert name=='colzero' and true_col_names==col_names and true_zero_counts==zero_counts and true_zero_fracs == zero_fracs and true_col_means==col_means and true_nonzero_col_means==nonzero_col_means

#test that JSON output for rowzero function is correct
def test_stats_rowzero_JSON():
	test = open('tests/stats/fake_counts_rowzero.json', 'r')
	for line in test:
		json_output = json.loads(line)
	
	name = json_output.get('name')
	zeros = json_output.get('stats', {}).get('zeros')

	true_row_names = ['gene1', 'gene2', 'gene3', 'gene4', 'gene5']

	row_names = []
	for i in range(0, len(zeros)):
		row = zeros[i]
		row_name = row.get('name')
		row_names.append(row_name)
	
	true_zero_counts = [1, 2, 2, 1, 0]

	zero_counts = []
	for i in range(0, len(zeros)):
		row = zeros[i]
		zero_count = row.get('zero_count')
		zero_counts.append(zero_count)
	
	true_zero_fracs = [1/3, 2/3, 2/3, 1/3, 0]

	zero_fracs = []
	for i in range(0, len(zeros)):
		row = zeros[i]
		zero_frac = row.get('zero_frac')
		zero_fracs.append(zero_frac)

	true_row_means = [(2+4)/3, 9/3, 4/3, (5+125)/3, (6+36+216)/3]
	
	row_means = []
	for i in range(0, len(zeros)):
		row = zeros[i]
		row_mean = row.get('mean')
		row_means.append(row_mean)

	true_nonzero_row_means = [(2+4)/2, 9, 4, (5+125)/2, (6+36+216)/3]

	nonzero_row_means = []
	for i in range(0, len(zeros)):
		row = zeros[i]
		nonzero_row_mean = row.get('nonzero_mean')
		nonzero_row_means.append(nonzero_row_mean)

	assert name=='rowzero' and true_row_names==row_names and true_zero_counts==zero_counts and true_zero_fracs == zero_fracs and true_row_means==row_means and true_nonzero_row_means==nonzero_row_means

#test that JSON output for entropy function is correct
def test_stats_entropy_JSON():
	test = open('tests/stats/fake_counts_entropy.json', 'r')
	for line in test:
		json_output = json.loads(line)
	
	name = json_output.get('name')
	entropies = json_output.get('stats', {}).get('entropies')

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

	assert name=='entropy' and true_entropies==row_entropies

#test that all functions were written to JSON output when summary is called
def test_stats_summary_JSON():
	test = open('tests/stats/fake_counts_summary.json', 'r')
	
	true_funcs = ['base', 'coldist', 'rowdist', 'colzero', 'rowzero', 'entropy']

	funcs = []
	for line in test:
		funcs.append(json.loads(line))

	names = []
	for func in funcs:
		name = func['name']
		names.append(name)

	assert true_funcs==names

def test_stats_PCA_name(fake_counts_obj):
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
    true_projections = [[0.57528892, 0.58086251, 0.57588315],
                        [-0.72606076, 0.03842312, 0.68655622],
                        [0.37666754, -0.81309434, 0.44384587]]
    projections = []
    components = output.get('components')
    for item in components:
      projections.append(item.get('projections'))
    assert np.allclose(true_projections, projections)
