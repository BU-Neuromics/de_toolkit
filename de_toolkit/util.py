from .common import CountMatrixFile
from .patsy_lite import ModelError
from contextlib import contextmanager

#https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ.get('PATH','').split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

class Stub(Exception): pass
def stub(f) :
  def stub(*args,**kwargs) :
    raise Stub('Not yet implemented - {}.{}'.format(f.__module__,f.__name__))
  return stub
