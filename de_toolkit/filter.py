'''
Usage:
    detk-filter [options] <command> [--column-data=<column data fn>] <counts_fn>

Options:
    -o <out_fn> --output=<out_fn>    Name of output file
'''

import numpy as np
import pandas as pd
from docopt import docopt
from .common import *
import os.path
import csv
import ply.lex as lex

#Available tokens for mini language
tokens = ('ALL', 'RELATION', 'NUMBER', 'MEDIAN', 'MEAN', 
          'NONZERO', 'ZEROS', 'CONDITION', 'OR', 'AND')

#Definitions of the mini language tokens
t_ALL = r'(?i)all'
t_RELATION = r'[<>]=?|='
t_MEDIAN = r'(?i)median'
t_MEAN = r'(?i)mean'
t_NONZERO = r'(?i)nonzero'
t_ZEROS = r'(?i)zeros'
t_CONDITION = r'(?i)condition\s?(\[[^\)]+\]\s?)?'
t_OR = r'(?i)or'
t_AND = r'(?i)and'

#Definition of number token 
def t_NUMBER(t):
    r'(\d+[\/\d. ]*|\d)'
    if '/' in t.value:
      num, den = t.value.split('/')
      t.value = float(num)/float(den)
    else:
      t.value = float(t.value)
    return t

#Mini language ignores spaces, tabs, brackets, and parentheses
t_ignore = ' \t[]()'

#Prints an error message if there's an invalid token
def t_error(t):
    print('Illegal character {}'.format(t.value[0]))
    t.lexer.skip(1)

#Helper method to evaluate the inequality based on the given relation
def evaluate_inequality(num1, relation, num2):
    if relation == '<' and num1 < num2:
      return True
    elif relation == '<=' and num1 <= num2:
      return True
    elif relation == '>' and num1 > num2:
      return True
    elif relation == '>=' and num1 >= num2:
      return True
    elif relation in ('=', '==') and num1 == num2:
      return True

    return False

def filter_nonzero(count_mat,n,relation,groups=None) :
    '''
      Filter rows from *count_mat* based on the number of nonzero counts.

      * if 0 < *n* < 1, then *n* is the fraction of samples that must be non-zero
      * if 1 <= *n* < *count_mat.shape[1]*, then *n* is the number of samples that
        must be non-zero
      * if *groups* is not *None*, it must be a list of column indices or names of
        samples that should be considered a group, and n is applied to each
        group separately. Rows are filtered if all groups fail the criterion based
        on *n*
     '''

    #Get counts, column names, and row names
    cnts = count_mat.counts.values
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names

    #Create dataframe for output
    final_cnts = pd.DataFrame(columns=column_names)

    #Applies filter to all samples
    if groups is None:

      #Filter by the fraction of samples that are nonzero
      if 0 <= n < 1:
        for item, name in zip(cnts, row_names):
          if evaluate_inequality(np.count_nonzero(item)/len(item), relation, n) is True:
            final_cnts.loc[name] = list(item)

      #Filter by the number of samples that are nonzero
      elif 1 <= n <= len(cnts[0]):
        for item, name in zip(cnts, row_names):
          if evaluate_inequality(np.count_nonzero(item), relation, n) is True:
            final_cnts.loc[name] = list(item)

    #Apply the filter to rows based on condition given
    else:

      #Keep track of rows to keep
      row_indices = []

      #Loop through the groups, apply filter to each separately
      for group in groups:
        group_df = count_mat.counts[group]
        for row_index, item in enumerate(group_df.values):

          #Filter by the fraction of samples that are nonzero
          if 0 <= n < 1:
            if evaluate_inequality(np.count_nonzero(item)/len(item), relation, n) is True:
              row_indices.append(row_index)

          #Filter by the number of samples that are nonzero
          elif 1 <= n <= len(cnts[0]):
            if evaluate_inequality(np.count_nonzero(item), relation, n) is True:
              row_indices.append(row_index)

      #Extract rows that should be kept and add to final dataframe      
      row_indices = set(row_indices)
      row_indices = sorted(row_indices)
      for index in row_indices:
        final_cnts = final_cnts.append(count_mat.counts.iloc[[index]])

    return final_cnts

def filter_zeros(count_mat,n,relation,groups=None) :
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

    #Get counts, column names, and row names
    cnts = count_mat.counts.values
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names

    #Create dataframe for output
    final_cnts = pd.DataFrame(columns=column_names)

    #Applies filter to all samples
    if groups is None:

      #Filter by the fraction of samples that are zero
      if 0 <= n < 1:
        for item, name in zip(cnts, row_names):
          if evaluate_inequality(list(item).count(0)/len(item), relation, n) is True:
            final_cnts.loc[name] = list(item)

      #Filter by the number of samples that are zero
      elif 1 <= n <= len(cnts[0]):
        for item, name in zip(cnts, row_names):
          if evaluate_inequality(list(item).count(0), relation, n) is True:
            final_cnts.loc[name] = list(item)

    #Apply the filter to rows based on condition given
    else:

      #Keep track of rows to keep
      row_indices = []

      #Loop through the groups, apply filter to each separately
      for group in groups:
        group_df = count_mat.counts[group]
        for row_index, item in enumerate(group_df.values):

          #Filter by the fraction of samples that are zero
          if 0 <= n < 1:
            if evaluate_inequality(list(item).count(0)/len(item), relation, n) is True:
              row_indices.append(row_index)

          #Filter by the number of samples that are zero
          elif 1 <= n <= len(cnts[0]):
            if evaluate_inequality(list(item).count(0), relation, n) is True:
              row_indices.append(row_index)
      
      #Extract rows that should be kept and add to final dataframe  
      row_indices = set(row_indices)
      row_indices = sorted(row_indices)
      for index in row_indices:
        final_cnts = final_cnts.append(count_mat.counts.iloc[[index]])

    return final_cnts


def filter_median(count_mat, num, relation, groups=None):
    '''
      Filter rows from *count_mat* based on the median.

      * if *groups* is not *None*, it must be a list of column indices or names of
        samples that should be considered a group, and n is applied to each
        group separately. Rows are filtered if all groups fail the criterion based
        on *num*
    '''

    #Get counts, column names, and row names
    cnts = count_mat.counts.values
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names

    #Create dataframe for output
    final_cnts = pd.DataFrame(columns=column_names)

    #Applies filter to all samples
    if groups is None:
      for item, name in zip(cnts, row_names):
        if evaluate_inequality(np.median(item), relation, num) is True:
          final_cnts.loc[name] = list(item) 

    #Apply the filter to rows based on condition given
    else:

      #Keep track of rows to keep
      row_indices = []

      #Loop through the groups, apply filter to each separately
      for group in groups:
        group_df = count_mat.counts[group]
        for row_index, item in enumerate(group_df.values):
          if evaluate_inequality(np.median(item), relation, num) is True:
            row_indices.append(row_index)

      #Extract rows that should be kept and add to final dataframe  
      row_indices = set(row_indices)
      row_indices = sorted(row_indices)
      for index in row_indices:
        final_cnts = final_cnts.append(count_mat.counts.iloc[[index]])

    return final_cnts

def filter_mean(count_mat, num, relation, groups=None):
    '''
      Filter rows from *count_mat* based on the mean.

      * if *groups* is not *None*, it must be a list of column indices or names of
        samples that should be considered a group, and n is applied to each
        group separately. Rows are filtered if all groups fail the criterion based
        on *num*
    '''

    #Get counts, column names, and row names
    cnts = count_mat.counts.values
    column_names = count_mat.sample_names
    row_names = count_mat.feature_names

    #Create dataframe for output
    final_cnts = pd.DataFrame(columns=column_names)

    #Applies filter to all samples
    if groups is None:
      for item, name in zip(cnts, row_names):
        if evaluate_inequality(np.mean(item), relation, num) is True:
          final_cnts.loc[name] = list(item)
 
    #Apply the filter to rows based on condition given
    else:

      #Keep track of rows to keep
      row_indices = []

      #Loop through the groups, apply filter to each separately
      for group in groups:
        group_df = count_mat.counts[group]
        for row_index, item in enumerate(group_df.values):
          if evaluate_inequality(np.mean(item), relation, num) is True:
            row_indices.append(row_index)

      #Extract rows that should be kept and add to final dataframe  
      row_indices = set(row_indices)
      row_indices = sorted(row_indices)
      for index in row_indices:
        final_cnts = final_cnts.append(count_mat.counts.iloc[[index]])
   
    return final_cnts
     
def main(argv=None):

    #Create command line arguments to pass in data and filter command
    args = docopt(__doc__, argv=argv)

    #Create CountMatrixFile object from given data
    args['<counts_fn>'] = args.get('<counts_fn>')
    counts_obj = CountMatrixFile(args['<counts_fn>'])
    
    #Get column data, if provided
    args['--column-data'] = args.get('--column-data')
    if args['--column-data'] is None:
      args['--column-data'] = ''

    #Get filter command and input to lexer
    command = args['<command>']
    lexer = lex.lex()
    lexer.input(command)

    #Parse through tokens of command and keep track of each term
    terms = []
    while True:
      tok = lexer.token()
      if not tok:
        break
      if tok.type == 'NUMBER':
        term['number'] = tok.value
      elif tok.type in ('MEDIAN', 'MEAN', 'NONZERO', 'ZEROS'):
        term = {}
        term['function'] = tok.value.lower()
      elif tok.type == 'RELATION':
        term['relation'] = tok.value
      elif tok.type in ('ALL', 'CONDITION'):
        term['condition'] = tok.value.lower()
        if '[' in term['condition']: 
          term['condition'] = term['condition'][term['condition'].find('[')+1:term['condition'].find(']')]
      elif tok.type in ('OR', 'AND'):
        term['next'] = tok.value.lower()
        terms.append(term)
    terms.append(term)

    #Find filtered output for each term
    filtered_data = []
    for term in terms:
      if term['condition'] == 'all':
        groups=None
      elif term['condition'] == 'condition':
        col_data = pd.read_csv(args['--column-data'], sep=None, engine='python')
        vals = col_data.iloc[:,1].unique()
        groups = [[] for i in range(len(vals))]
        for i in range(0, len(vals)):
          col_case = col_data.loc[col_data.iloc[:,1] == vals[i]]
          groups[i] = col_case.iloc[:,0].tolist()
      else:
        col_data = pd.read_csv(args['--column-data'], sep=None, engine='python')
        groups = []
        col_case = col_data.loc[col_data.iloc[:,1] == term['condition']]
        groups.append(col_case.iloc[:,0].tolist())

      if term['function'] == 'median':
        output = filter_median(counts_obj, term['number'], term['relation'], groups)
      elif term['function'] == 'mean':
        output = filter_mean(counts_obj, term['number'], term['relation'], groups)
      elif term['function'] == 'nonzero':
        output = filter_nonzero(counts_obj, term['number'], term['relation'], groups)
      elif term['function'] == 'zeros':
        output = filter_zeros(counts_obj, term['number'], term['relation'], groups)

      filtered_data.append(output)

    #Get the final output determined by and or or keywords
    final_data = filtered_data[0]
    i = 1
    for term in terms:
      if 'next' in term:
        if term['next'] == 'or':
          final_data = pd.concat([final_data, filtered_data[i]])
        elif term['next'] == 'and':
          final_data = final_data.reset_index().merge(filtered_data[i], how='left').set_index('index')
        i+=1 

    #Obtain string used to name output files, unless filename is specified
    output_fn = args.get('--output')
    if output_fn is None:
      filename_prefix = os.path.splitext(args['<counts_fn>'])
      output_fn = filename_prefix[0]+'_filtered'+filename_prefix[1]

    #Get first column name and delimiter to use in output   
    with open(args['<counts_fn>']) as f:
      dialect = csv.Sniffer().sniff(f.read())
      f.seek(0)
      first_line = f.readline()
      index = first_line.find(dialect.delimiter)
      first_val = first_line[0:index]

    #Write final filtered output to the output file
    with open(output_fn, 'w') as out_f:
      final_data.index.names = [first_val]
      final_data.to_csv(out_f, sep=dialect.delimiter)

if __name__ == '__main__':
    main()
