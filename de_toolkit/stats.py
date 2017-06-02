import json

'''
Usage:
	detk-stats summary [options] <counts_fn>
	detk-stats base <counts_fn>
	detk-stats dist [options] <counts_fn>
	detk-stats pca [options] <counts_fn>

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

def dist(count_mat) :
	'''Distribution plots and statistics of counts'''
	pass

def pca(count_mat) :
	'''PCA plots and statistics of counts'''
	pass
