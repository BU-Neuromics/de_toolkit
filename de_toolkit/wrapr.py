'''
Usage: detk-wrapr [options] <rscript> <counts_in> <counts_out>
       [--meta-in=<metadata_in>]  [--meta-out=<metadata_out>]
       [--params-in=<params_in>] [--params-out=<params_out>]

Options:
    --rpath=PATH     Path to Rscript executable, inferred from the environment
                     by default
'''
from collections import defaultdict
import json
import os
import pandas as pd
import subprocess
from tempfile import NamedTemporaryFile
from .common import CountMatrixFile
from .util import which

class RscriptExecutableNotFound(Exception) : pass
class RPackageMissing(Exception) : pass
class RExecutionError(Exception) : pass

def get_r_path():
    'Return the path to Rscript found in the shell environment.'
    return which('Rscript')

def check_r() :
    'Tests whether the Rscript executable can be found.'
    return get_r_path() is not None

def check_jsonlite():
    '''Tests whether the R package jsonlite is installed. jsonlite is 
    required for the wrapr interface.'''
    return subprocess.run([
        get_r_path(),
        '-e',
        '"library(jsonlite)"'
        ]).returncode == 0

def require_r(f):
    '''Decorator for functions that require using R. Raises exception if
    either Rscript or jsonlite package cannot be found.'''
    def _f(*args,**kwargs):
        if not check_r():
            raise RscriptExecutableNotFound('Rscript executable could not be '
                    'found on PATH. Rscript is needed for this functionality')
        elif not check_jsonlite():
            raise RPackageMissing('R package jsonlite is needed for this '
                    'functionality. In R, try installing with:\n\n'
                    'install.packages("jsonlite")')
        else :
            return f(*args,**kwargs)
    return _f

def check_deseq2():
    'Tests whether the DESeq2 bioconductor package is installed.'
    wr = wrapr('library(DESeq2)')
    return wr.success

@require_r
def require_deseq2(f):
    '''Decorator for functions that require using DESeq2. Raises exception if
    the package cannot be found.'''
    def _f(*args,**kwargs):
        if not check_deseq2():
            raise RPackageMissing('R package DESeq2 is needed for this '
                    'functionality. In R, try installing with:\n\n'
                    'source("http://bioconductor.org/biocLite.R")\n'
                    'biocLite("DESeq2")')
        else :
            return f(*args,**kwargs)
    return _f
   

_script_tmpl = '''\
args <- commandArgs(trailingOnly=TRUE)
counts.fn <- args[1]; metadata.fn <- args[2]; params.fn <- args[3];
counts.out.fn <- args[4]; metadata.out.fn <- args[5]; params.out.fn <- args[6];
library(jsonlite)
json <- readChar(params.fn, file.info(params.fn)$size)
params <- if(nchar(json) > 0) {{
    read_json(params.fn,simplifyVector=TRUE)
}} else {{
    list()
}}

{script}
'''
class WrapR(object) :
    '''
    Wrapper object for calling R code with Rscript.
    '''
    def __init__(self,
            rscript_path,
            counts=None,
            metadata=None,
            params=None,
            counts_out_fn=None,
            metadata_out_fn=None,
            params_out_fn=None,
            rpath=None,
            raise_on_error=True
            ) :

        self._files = {}
        self._paths = defaultdict(str)

        # custom rpath
        self._paths['rpath'] = rpath or get_r_path()

        # load script code and put into the template that defines convenience
        # in/out filename variables
        with NamedTemporaryFile('wt',delete=False) as f :
            self._files['rscript'] = f
            self._paths['rscript'] = f.name
            with open(os.path.realpath(rscript_path),'rt') as f_in :
                f.write(_script_tmpl.format(script=f_in.read()))
            f.flush()

        # write counts to tempfile
        with NamedTemporaryFile('wt',delete=False) as f :
            self._files['counts_in'] = f
            self._paths['counts_in'] = f.name
            if counts is not None :
                counts.to_csv(self._files['counts_in'])
                f.flush()

        # set counts output file if provided, otherwise create temp file
        self._paths['counts_out'] = counts_out_fn
        if counts_out_fn is None :
            self._files['counts_out'] = NamedTemporaryFile('wt',delete=False)
            self._paths['counts_out'] = self._files['counts_out'].name

        # write metadata to tempfile if provided
        with NamedTemporaryFile('wt',delete=False) as f :
            self._files['meta_in'] = f
            self._paths['meta_in'] = f.name
            if metadata is not None :
                metadata.to_csv(self._files['meta_in'])
                f.flush()

        # set metadata output file if provided, otherwise create temp file
        self._paths['meta_out'] = metadata_out_fn
        if metadata_out_fn is None :
            self._files['meta_out'] = NamedTemporaryFile('wt',delete=False)
            self._paths['meta_out'] = self._files['meta_out'].name

        # write out params json if provided
        with NamedTemporaryFile('wt',delete=False) as f :
            self._files['params_in'] = f
            self._paths['params_in'] = f.name
            if params is not None :
                json.dump(params,f)
                f.flush()

        self._paths['params_out'] = params_out_fn
        if params_out_fn is None :
            self._files['params_out'] = NamedTemporaryFile('wt',delete=False)
            self._paths['params_out'] = self._files['params_out'].name

        # initialize output members
        self.counts_out = None
        self.metadata_out = None
        self.params_out = None

        self.raise_on_error = raise_on_error

    @require_r
    def execute(self) :
        '''Execute the R script and load in the resulting output files, if
        any.'''

        # construct Rscript command
        cmd = ('{rpath} --vanilla {rscript} {counts_in} {meta_in} {params_in} '
               '{counts_out} {meta_out} {params_out}').format(
                    **self._paths
               ).split(' ')

        # run the R script
        p = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
        )

        self.process = p
        self.stdout = p.stdout.decode()
        self.stderr = p.stderr.decode()
        self.returncode = p.returncode
        self.success = p.returncode == 0

        if self.raise_on_error and not self.success :
            raise RExecutionError('R encountered an error:\n\n' +
                    'stdout:\n{}\n\n'.format(self.stdout) +
                    'stderr:\n{}\n'.format(self.stderr)
                )

        # read in the outputs
        if os.path.exists(self._paths['counts_out']) :
            try :
                self.counts_out = pd.read_csv(
                    self._paths['counts_out'],
                    index_col=0
                )
            except pd.errors.EmptyDataError :
                pass

        if os.path.exists(self._paths['meta_out']) :
            try :
                self.metadata_out = pd.read_csv(
                    self._paths['meta_out'],
                    index_col=0
                )
            except pd.errors.EmptyDataError :
                pass

        if os.path.exists(self._paths['params_out']) :
            with open(self._paths['params_out'],'rt') as f :
                json_str = f.read()
                if len(json_str) > 0 :
                    self.params_out = json.loads(json_str)

                    # jsonlite puts all elements of lists into arrays,
                    # recurse through params and replace length 1 lists
                    # with the value
                    def flat(e) :
                        if isinstance(e, dict) :
                            return {k:flat(v) for k,v in e.items()}
                        elif isinstance(e, list) :
                            if len(e) == 1 :
                                return flat(e[0])
                            else :
                                return [flat(_) for _ in e]
                        else :
                            return e
                    self.params_out = flat(self.params_out)

    def __enter__(self) :
        return self
    def __exit__(self,*args)  :
        # clean up the temp files
        for k,f in self._files.items() :
            os.remove(f.name)

def wrapr(Rcode,**kwargs) :
    '''Convenience wrapper for WrapR object. Writes *Rcode* to a temporary file
    and executes it as it would if it were provided.

    Returns a WrapR object.
    '''

    with NamedTemporaryFile('wt') as f :
        f.write(Rcode)
        f.flush()
        wr = WrapR(
            f.name,
            **kwargs
        )
        wr.execute()
        return wr

def main(argv=None) :

    args = docopt(__doc__,argv=argv)

    counts_obj = CountMatrixFile(
          args['<counts_in>'],
          args['<metadata_in>'],
          strict=args.get('--strict',False)
    )

    params = None
    if os.path.exists(args['<params_in>']) :
        with open(args['<params_in>'],'rt') as f :
            params = json.load(f)

    with WrapR(
        args['<rscript>'],
        counts_obj.counts,
        counts_obj.column_data,
        params=params,
        counts_out_fn=args['<counts_out>'],
        metadata_out_fn=args['<metadata_out>'],
        params_out_fn=args['<params_out>'],
        rpath=args['--rpath']
        ) as wr :
        wr.execute()

if __name__ == '__main__' :

  main()
