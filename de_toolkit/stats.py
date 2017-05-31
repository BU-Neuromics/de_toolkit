'''
Usage:
  detk-stats summary [options] <counts_fn>
  detk-stats dist [options] <counts_fn>
  detk-stats pca [options] <counts_fn>

Options:
  -o FILE --output=FILE    Destination of primary output [default: stdout]

'''
from docopt import docopt

def summary(count_mat) :
  pass

def dist(count_mat) :
  '''Distribution plots and statistics of counts'''
  pass

def pca(count_mat) :
  '''PCA plots and statistics of counts'''
  pass
