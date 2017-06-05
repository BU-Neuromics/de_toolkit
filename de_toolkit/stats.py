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
	cnts=[[2,4,8],[1,1,1],[1,1,1],[1,1,1],[1,1,1]]
	#cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)

	output={}
	output['name'] = 'base'
	output['stats'] = {}
	output['stats']['num_cols'] = num_cols
	output['stats']['num_rows'] = num_rows

	return json.dumps(output, sort_keys=True, indent=4)

def coldist(count_mat) :
	'''Column-wise distribution of counts'''
	pass

def rowdist(count_mat) :
	'''Row-wise distribution of counts'''
	pass

def colzero(count_mat) :
	'''Column-wise distribution of zero counts'''
	
	cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)
	
	zero_counts =[]
	for i in range(0, num_cols):
		zero_count = 0
		for j in range(0, num_rows):
			if cnts[j][i]==0:
				zero_count+=1
		zero_counts.append(zero_count)

	output={}
	output['name'] = 'colzero'
	output['stats'] = {}
	output['stats']['zeros'] = []
	
	return output

def rowzero(count_mat) :
	'''Row-wise distribution of zero counts'''
	pass

def entropy(count_mat) :
	'''Row-wise sample entropy calculation'''
	pass

