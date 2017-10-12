'''
Usage:
    detk-filter [options] nonzero [--n=<n>] [--groups=<groups>] <counts_fn>
'''

import numpy as np
import pandas as pd
from docopt import docopt
from .common import *

def filter_nonzero(count_mat,n=0.5,groups=None) :
    '''
      Filter rows from *count_mat* based on the number of zero counts.

      * if 0 < *n* < 1, then *n* is the fraction of samples that must be non-zero
      * if 1 <= *n* < *count_mat.shape[1]*, then *n* is the number of samples that
        must be non-zero
      * if *groups* is not *None*, it must be a list of column indices or names of
        samples that should be considered a group, and n is applied to each
        group separately. Rows are filtered if all groups fail the criterion based
        on *n*
     '''

    cnts = count_mat.counts.as_matrix()
    column_names = count_mat.sample_names
    row_names = list(count_mat.count_names)
    final_cnts = pd.DataFrame(columns=column_names)

    if groups is None:
      if 0 < n < 1:
        for item, name in zip(cnts, row_names):
          if np.count_nonzero(item)/len(item) > n:
            final_cnts.loc[name] = list(item)
    
      elif 1 <= n <= len(cnts[0]):
        for item, name in zip(cnts, row_names):
          if np.count_nonzero(item) >= n:
            final_cnts.loc[name] = list(item)

    return final_cnts

def main(argv=None):

    args = docopt(__doc__, argv=argv)

    args['<counts_fn>'] = args.get('<counts_fn>')
    counts_obj = CountMatrixFile(args['<counts_fn>'])

    args['--n'] = args.get('--n')
    if args['--n'] is None:
      args['--n'] = 0.5
    else:
      args['--n'] = float(args['--n'])
    
    args['--groups'] = args.get('--groups')

    if args['nonzero']:
      output = filter_nonzero(counts_obj, args['--n'], args['--groups'])


if __name__ == '__main__':
    main()
