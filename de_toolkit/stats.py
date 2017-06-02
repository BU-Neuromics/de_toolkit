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
	cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)
	output=[num_cols,num_rows]
	return output

def coldist(count_mat) :
	'''Column-wise distribution of counts'''
	pass

def rowdist(count_mat) :
	'''Row-wise distribution of counts'''
	pass

def colzero(count_mat) :
	'''Column-wise distribution of zero counts'''
	pass

def rowzero(count_mat) :
	'''Row-wise distribution of zero counts'''
	pass

def entropy(count_mat) :
	'''Row-wise sample entropy calculation'''
	pass
