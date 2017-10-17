'''
Usage:
    detk-filter [options] <command> <counts_fn>

Options:
    --output=<out_fn>    Name of output file
'''

import numpy as np
import pandas as pd
from docopt import docopt
from .common import *
import os.path
import csv
import ply.lex as lex

tokens = ('ALL', 'RELATION', 'NUMBER', 'PAREN', 'MEDIAN', 'MEAN', 'NONZERO', 'ZEROS')

t_ALL = r'(?i)all'
t_RELATION = r'[<>]=?|='
t_PAREN = t_PAREN = r'(\(|\))'
t_MEDIAN = r'(?i)median'
t_MEAN = r'(?i)mean'
t_NONZERO = r'(?i)nonzero'
t_ZEROS = r'(?i)zeros'

def t_NUMBER(t):
    r'[-+]?([0-9]*\.[0-9]+|[0-9]+)'
    t.value = float(t.value)
    return t

t_ignore = ' \t'

def t_error(t):
    filter.append('Illegal character {}'.format(t.value[0]))
    t.lexer.skip(1)

def filter_nonzero(count_mat,n,relation,groups=None) :
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
    row_names = count_mat.feature_names
    final_cnts = pd.DataFrame(columns=column_names)

    if groups is None:
      if 0 < n < 1:
        for item, name in zip(cnts, row_names):
          if relation == '>':
            if np.count_nonzero(item)/len(item) > n:
              final_cnts.loc[name] = list(item)
          elif relation == '>=':
            if np.count_nonzero(item)/len(item) >= n:
              final_cnts.loc[name] = list(item)
          elif relation == '<':
            if np.count_nonzero(item)/len(item) < n:
              final_cnts.loc[name] = list(item)
          elif relation == '<=':
            if np.count_nonzero(item)/len(item) <= n:
              final_cnts.loc[name] = list(item)
          elif relation == '=' or relation == '==':
            if np.count_nonzero(item)/len(item) == n:
              final_cnts.loc[name] = list(item)     

      elif 1 <= n <= len(cnts[0]):
        for item, name in zip(cnts, row_names):
          if relation == '>':
            if np.count_nonzero(item) > n:
              final_cnts.loc[name] = list(item)
          elif relation == '>=':
            if np.count_nonzero(item) >= n:
              final_cnts.loc[name] = list(item)
          elif relation == '<':
            if np.count_nonzero(item) < n:
              final_cnts.loc[name] = list(item)
          elif relation == '<=':
            if np.count_nonzero(item) <= n:
              final_cnts.loc[name] = list(item)
          elif relation == '=' or relation == '==':
            if np.count_nonzero(item) == n:
              final_cnts.loc[name] = list(item)     

    return final_cnts

def filter_zeros(count_mat,n,relation,groups=None) :

    cnts = count_mat.counts.as_matrix()
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names
    final_cnts = pd.DataFrame(columns=column_names)

    if groups is None:
      if 0 < n < 1:
        for item, name in zip(cnts, row_names):
          if relation == '>':
            if 1-np.count_nonzero(item)/len(item) > n:
              final_cnts.loc[name] = list(item)
          elif relation == '>=':
            if 1-np.count_nonzero(item)/len(item) >= n:
              final_cnts.loc[name] = list(item)
          elif relation == '<':
            if 1-np.count_nonzero(item)/len(item) < n:
              final_cnts.loc[name] = list(item)
          elif relation == '<=':
            if 1-np.count_nonzero(item)/len(item) <= n:
              final_cnts.loc[name] = list(item)
          elif relation == '=' or relation == '==':
            if 1-np.count_nonzero(item)/len(item) == n:
              final_cnts.loc[name] = list(item)     

      elif 1 <= n <= len(cnts[0]):
        for item, name in zip(cnts, row_names):
          if relation == '>':
            if len(item)-np.count_nonzero(item) > n:
              final_cnts.loc[name] = list(item)
          elif relation == '>=':
            if len(item)-np.count_nonzero(item) >= n:
              final_cnts.loc[name] = list(item)
          elif relation == '<':
            if len(item)-np.count_nonzero(item) < n:
              final_cnts.loc[name] = list(item)
          elif relation == '<=':
            if len(item)-np.count_nonzero(item) <= n:
              final_cnts.loc[name] = list(item)
          elif relation == '=' or relation == '==':
            if len(item)-np.count_nonzero(item) == n:
              final_cnts.loc[name] = list(item)     

    return final_cnts


def filter_median(count_mat, num, relation):
    
    cnts = count_mat.counts.as_matrix()
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names
    final_cnts = pd.DataFrame(columns=column_names)

    for item, name in zip(cnts, row_names):
      if relation == '>':
        if np.median(item) > num:
          final_cnts.loc[name] = list(item)
      elif relation == '>=':
        if np.median(item) >= num:
          final_cnts.loc[name] = list(item)
      elif relation == '<':
        if np.median(item) < num:
          final_cnts.loc[name] = list(item)
      elif relation == '<=':
        if np.median(item) <= num:
          final_cnts.loc[name] = list(item)
      elif relation == '=' or relation == '==':
        if np.median(item) == num:
          final_cnts.loc[name] = list(item)

    return final_cnts

def filter_mean(count_mat, num, relation):

    cnts = count_mat.counts.as_matrix()
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names
    final_cnts = pd.DataFrame(columns=column_names)

    for item, name in zip(cnts, row_names):
      if relation == '>':
        if np.mean(item) > num:
          final_cnts.loc[name] = list(item)
      elif relation == '>=':
        if np.mean(item) >= num:
          final_cnts.loc[name] = list(item)
      elif relation == '<':
        if np.mean(item) < num:
          final_cnts.loc[name] = list(item)
      elif relation == '<=':
        if np.mean(item) <= num:
          final_cnts.loc[name] = list(item)
      elif relation == '=' or relation == '==':
        if np.mean(item) == num:
         final_cnts.loc[name] = list(item)

    return final_cnts
     
def main(argv=None):

    args = docopt(__doc__, argv=argv)

    args['<counts_fn>'] = args.get('<counts_fn>')
    counts_obj = CountMatrixFile(args['<counts_fn>'])

    command = args['<command>']
    lexer = lex.lex()
    lexer.input(command)

    while True:
      tok = lexer.token()
      if not tok:
        break
      if tok.type == 'NUMBER':
        number = tok.value
      elif tok.type in ('MEDIAN', 'MEAN', 'NONZERO', 'ZEROS'):
        function = tok.value.lower()
      elif tok.type == 'RELATION':
        relation = tok.value

    if function == 'median':
      output = filter_median(counts_obj, number, relation)
    elif function == 'mean':
      output = filter_mean(counts_obj, number, relation)
    elif function == 'nonzero':
      output = filter_nonzero(counts_obj, number, relation)
    elif function == 'zeros':
      output = filter_zeros(counts_obj, number, relation)

    output_fn = args.get('--output')
    if output_fn is None:
      filename_prefix = os.path.splitext(args['<counts_fn>'])
      output_fn = filename_prefix[0]+'_filtered'+filename_prefix[1]
    
    with open(args['<counts_fn>']) as f:
      dialect = csv.Sniffer().sniff(f.read())
      f.seek(0)
      first_line = f.readline()
      index = first_line.find(dialect.delimiter)
      first_val = first_line[0:index]

    with open(output_fn, 'w') as out_f:
      output.index.names = [first_val]
      output.to_csv(out_f, sep=dialect.delimiter)

if __name__ == '__main__':
    main()
