from .common import CountMatrix

def load_count_mat_file(count_fn) :
  with open(count_fn) as f :
    count_obj = CountMatrix(f)
  return count_obj

def require_rpy2(f) :
  try :
    import rpy2
  except ImportError as e :
    raise Exception('rpy2 must be installed to use this function')

  return f

class Stub(Exception): pass
def stub(f) :
  def stub(*args,**kwargs) :
    raise Stub('Not yet implemented - {}.{}'.format(f.__module__,f.__name__))
  return stub
