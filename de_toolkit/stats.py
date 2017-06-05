import json

'''
Usage:
	detk-stats summary [options] <counts_fn>
	detk-stats base <counts_fn>
	detk-stats coldist [options] [--bins=<bins>] [--log] [--density] <counts_fn>
	detk-stats rowdist [options] [--bins=<bins>] [--log] [--density] <counts_fn>
	detk-stats [options] colzero <counts fn>
	detk-stats [options] rowzero <counts fn>
	detk-stats [options] entropy <counts fn>

Options:
	-o FILE --output=FILE    Destination of primary output [default: stdout]

'''
from docopt import docopt

def summary(count_mat) :
	pass

def base(count_mat) :
	'''Basic statistics of the counts file'''	
	
	#Get counts, number of columns, and number of rows
	cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)

	#Format output
	output={}
	output['name'] = 'base'
	output['stats'] = {}
	output['stats']['num_cols'] = num_cols
	output['stats']['num_rows'] = num_rows

	#Return output in JSON format
	return json.dumps(output, sort_keys=True, indent=4)

def coldist(count_mat) :
	'''Column-wise distribution of counts'''
	pass

def rowdist(count_mat) :
	'''Row-wise distribution of counts'''
	pass

def colzero(count_mat) :
	'''Column-wise distribution of zero counts'''
	
	#Get counts, number of columns, number of rows, and sample names
	cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)
	col_names=count_mat.sample_names

	#Calculate zero counts for each column
	zero_counts =[]
	for i in range(0, num_cols):
		zero_count = 0
		for j in range(0, num_rows):
			if cnts[j][i]==0:
				zero_count+=1
		zero_counts.append(zero_count)

	#Calculate zero fractions for each column
	zero_fracs = []
	for i in range(0, num_cols):
		zero_frac=zero_counts[i]/num_rows
		zero_fracs.append(zero_frac)
	
	#Calculate means for each column
	col_means = []
	for i in range(0, num_cols):
		mean = 0.0
		for j in range(0, num_rows):
			mean+=cnts[j][i]
		mean=mean/num_rows
		col_means.append(mean)

	#Calculate the means of only the nonzero counts in each column
	nonzero_col_means = []
	for i in range(0, num_cols):
		mean=0.0
		num=0
		for j in range(0, num_rows):
			if cnts[j][i] != 0:
				mean+=cnts[j][i]
				num+=1
		if num != 0:
			mean=mean/num
		nonzero_col_means.append(mean)

	#Format output
	output={}
	output['name'] = 'colzero'
	output['stats'] = {}
	output['stats']['zeros'] = []

	for i in range(0, num_cols):
		col = {}
		col['name'] = col_names[i]
		col['zero_count'] = zero_counts[i]
		col['zero_frac'] = zero_fracs[i]
		col['mean'] = col_means[i]
		col['nonzero_mean'] = nonzero_col_means[i]
		output['stats']['zeros'].append(col)
	
	#Return output in JSON format
	return json.dumps(output, sort_keys=True, indent=4)

def rowzero(count_mat) :
	'''Row-wise distribution of zero counts'''
	pass

def entropy(count_mat) :
	'''Row-wise sample entropy calculation'''
	pass

