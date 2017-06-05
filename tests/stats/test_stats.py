import docopt                                                                   
import numpy as np                                                              
import os                                                                       
import pandas                                                                   
import pytest                                                                   
import tempfile                       
import json                                          

from de_toolkit.stats import base                                                                               
#test for base function
def test_stats_base(fake_counts_obj): 
	json_output = base(fake_counts_obj)
	output=json.loads(json_output)
	cols = output.get('stats', {}).get('num_cols')
	rows = output.get('stats', {}).get('num_rows')
	assert cols==3 and rows==5 

from de_toolkit.stats import colzero

#test that colzero function gets correct column names
def test_stats_colzero_names(fake_counts_obj_with_zeros):
	json_output = colzero(fake_counts_obj_with_zeros)
	output=json.loads(json_output)
	zeros = output.get('stats', {}).get('zeros')

	true_col_names = fake_counts_obj_with_zeros.sample_names.tolist()
	
	col_names = []
	for i in range(0, len(zeros)):
		col = zeros[i]
		name = col.get('name')
		col_names.append(name)
	
	assert true_col_names==col_names

#test that colzero function gets correct zero counts
def test_stats_colzero_zero_counts(fake_counts_obj_with_zeros):
	json_output = colzero(fake_counts_obj_with_zeros)
	output=json.loads(json_output)
	zeros = output.get('stats', {}).get('zeros')

	true_zero_counts = [1, 2, 3]
	
	zero_counts = []
	for i in range(0, len(zeros)):
		col = zeros[i]
		zero_count = col.get('zero_count')
		zero_counts.append(zero_count)

	assert true_zero_counts==zero_counts
