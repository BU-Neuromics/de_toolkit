import numpy
import pandas
from patsy import EvalFactor, ModelDesc, design_matrix_builders, dmatrices
from ply import lex
import re

class PatsyLiteParseError(Exception): pass

tokens = ('CONSTANT','SIMPLETERM','BINARYTERM','FACTORTERM','RELATION','OP','COUNT')

t_COUNT = r'count'
t_CONSTANT = r'-?\d+(?:\.\d*)?'
t_SIMPLETERM = r'\w[\w:*.()]*'
t_RELATION = r'~'
t_OP = r'[-+*/]'
t_ignore = ' '

def t_BINARYTERM(t) :
  r'(\w+)\[(\w+)\]'
  t.term, t.args = t.lexer.lexmatch.groups()[1:3]
  return t

def t_FACTORTERM(t) :
  r'(\w+)\[((?:\w+,)+\w+)\]'
  # this regex returns a bunch of empty groups for some reason
  # filter out the None valued groups and just operate on what
  # is left
  groups = [_ for _ in t.lexer.lexmatch.groups() if _]
  t.term, t.args = groups[1], groups[2]
  t.args = t.args.split(',')
  return t

def t_error(t) :
  #print(t)
  return t

lexer = lex.lex()

def patsy_lite_to_patsy(formula) :

  # I guess we assume there is always a lhs and a rhs?
  if '~' not in formula :
    raise PatsyLiteParseError('A ~ must be specified, so that there is a left '
      'and right hand side')

  lexer.input(formula)

  patsy_formula = []
  # the name map is attached to the model description and used later to
  # replace the patsy DesignInfo column names to the originals specified
  # in the formula
  name_map = {}

  while True:

    try :
      tok = lexer.token()
    except lex.LexError as e :
      raise PatsyLiteParseError('Error parsing formula:',e.args)

    if not tok : break

    if tok.type in ('CONSTANT','SIMPLETERM','RELATION','OP','COUNT') :
      patsy_formula.append(tok.value)

    # term[ref] -> C(term, Treatment("ref"))
    if tok.type == 'BINARYTERM' :
      term = 'C({}, Treatment({}))'.format(tok.term,repr(tok.args))
      name_map[term] = tok.term
      patsy_formula.append(term)

    # term[lev1,lev2,lev3] -> C(term, levels=["lev1","lev2","lev3"])
    if tok.type == 'FACTORTERM' :
      term = 'C({}, levels={})'.format(tok.term,repr(tok.args))
      name_map[term] = tok.term
      patsy_formula.append(term)

  patsy_formula = ' '.join(patsy_formula)
  model = ModelDesc.from_formula(patsy_formula)
  model.name_map = name_map
  return model

def build_design_matrix(formula,data) :
  model = patsy_lite_to_patsy(formula)
  mat = dmatrices(model.describe(),data,return_type='dataframe')

  # th patsy formula names are ugly and not very machine (or human)
  # readable
  # replace the patsy names with the patsy lite names
  def rename_model_cols(c) :
    print
    for k,v in model.name_map.items() :
      if k in c :
        print('before:',c)
        c = c.replace(k,v)
        print('field replace:',c)
      # categorical variables sometimes look like
      # C(term, Treatment('cont'))[T.cont]
      # replace [T.cont] -> __cont
      cat_match = r'\[(?:T\.)?(.*)\]'
      if re.search(cat_match,c) :
        c = re.sub(cat_match,r'__\1',c)
        print('bracket replace:',c)
    return c

  mat[0].rename(columns=rename_model_cols,inplace=True)
  print(mat[0].columns)

  mat[1].rename(columns=rename_model_cols,inplace=True)
  print(mat[1].columns)

  return mat
