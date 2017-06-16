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

#test for base function
def test_stats_base(fake_counts_obj):
	output = base(fake_counts_obj)
	cols = output.get('stats', {}).get('num_cols')
	rows = output.get('stats', {}).get('num_rows')

	assert cols==3 and rows==5


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
	print(row_dist_func)

	row_dist_true = [[1.0 for i in range(20)] for j in range(3)]
	assert row_dist_func == row_dist_true


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
