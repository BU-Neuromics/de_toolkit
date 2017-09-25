import numpy
import pandas
from patsy import EvalFactor, ModelDesc, design_matrix_builders, dmatrices
from ply import lex
from pprint import pprint
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

class ModelError(Exception): pass

class DesignMatrix(object) :

  def __init__(self,formula,model_data) :

    # when there is a categorical veriable on the lhs, the vector
    # space of all levels is included where, for example, we're only
    # interested in the vector space of the reference level for
    # logistic regression (i.e., one column with zero for reference
    # samples and one for the other)
    # with patsy we can control this by adding an intercept to the
    # lhs, which will acheive the desired result and has no effect
    # when including, e.g. continuous variables
    # we remove the Intercept term from the lhs before returning
    # the design matrix
    formula = '1 + {}'.format(formula)

    model = patsy_lite_to_patsy(formula)
    self.lhs, self.rhs = dmatrices(
      model.describe()
      ,model_data
      ,return_type='dataframe'
    )

    #TODO remove log printing code when stable
    def log(*args) :
      if False :
        pprint(args)

    log(model.name_map)

    # the patsy formula names are ugly and not very machine (or human)
    # readable
    # replace the patsy names with the patsy lite names
    def rename_model_cols(c) :
      log('considering',c)
      log(model.name_map)
      for k,v in model.name_map.items() :
        log('searching for',k,'in',c)
        if k in c :
          log('before:',c)
          c = c.replace(k,v)
          log('field replace:',c)
      # categorical variables sometimes look like
      # C(term, Treatment('cont'))[T.cont]
      # replace [T.cont] -> __cont
      cat_match = r'\[(?:T\.)?(\w*)\]'
      if re.search(cat_match,c) :
        c = re.sub(cat_match,r'__\1',c)
        log('bracket replace:',c)
      return c

    self.lhs.rename(columns=rename_model_cols,inplace=True)
    self.rhs.rename(columns=rename_model_cols,inplace=True)

    # remove the Intercept term from the lhs that we added at the beginning
    self.drop_from_lhs('Intercept')

  @property
  def design(self) :
    return ' '.join([
      ' + '.join(self.lhs.columns),
      '~',
      ' + '.join(self.rhs.columns)
    ])

  def drop_from_lhs(self,column) :
    if column not in self.lhs :
      raise ModelError('Cannot drop {} from lhs, does not exist'.format(column))
    self.lhs.drop(column,axis=1,inplace=True)

  def drop_from_rhs(self,column) :
    if column not in self.rhs :
      raise ModelError('Cannot drop {} from rhs, does not exist'.format(column))
    self.rhs.drop(column,axis=1,inplace=True)

  def head(self) :
    return self.full_matrix.head()

  @property
  def full_matrix(self) :
    return pandas.concat([self.lhs,self.rhs],axis=1)
