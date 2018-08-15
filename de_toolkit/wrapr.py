'''
Usage:
    detk-wrapr check
    detk-wrapr run [options] <rscript> <counts_in> <out>

Options:
    --rpath=PATH       Path to Rscript executable, inferred from the environment
                       by default
    --meta-in=PATH     Path to metadata file corresponding to columns in counts,
                       same as is passed to other detk functions
    --meta-out=PATH    Path to metadata file corresponding to columns in counts,
                       same as is passed to other detk functions
    --params-in=PATH   Path to JSON formatted file containing parameters needed
                       by R script
    --params-out=PATH  Path to JSON formatted file to be created with output
                       from the R script
    --strict           Ensure counts column names and the first row of the
                       metadata file provided (if any) match, otherwise fail
'''
from collections import defaultdict
from docopt import docopt
import json
import os
import pandas as pd
import subprocess
import sys
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

def check_r_package(pkg) :
    'Tests whether the R package *pkg* is installed.'
    p = subprocess.run(' '.join([
        get_r_path(),
        '-e',
        '"library({})"'.format(pkg)
        ]),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    return p.returncode == 0

def require_r_package(pkg) :
    'Check whether pkg is installed in R, and raise if not.'
    if not check_r_package(pkg) :
        raise RPackageMissing(('R package {pkg} is needed for this '
                'functionality. In R, try installing with:\n\n'
                'install.packages("{pkg}")').format(pkg=pkg))

def require_r(*pkgs):
    '''Decorator for functions that require using R. Raises exception if
    either Rscript or jsonlite or other packages provided cannot be found.
    Can be called with or without arguments. When arguments are supplied,
    the arguments should be strings of names of R packages required by the
    decorated function.

    **Examples**

    @require_r
    def call_requiring_only_Rscript_and_jsonlite() :
        ...

    @require_r('logistf',...)
    def call_requiring_Rscript_jsonlite_and_logistf_and_others() :
        ...
    '''
    # when decorated without arguments
    if callable(pkgs[0]) :
        f = pkgs[0]
        def decorator(*args,**kwargs):
            if not check_r():
                raise RscriptExecutableNotFound('Rscript executable could not be '
                        'found on PATH. Rscript is needed for this functionality')
            require_r_package('jsonlite')
            return f(*args,**kwargs)
    # when decorated with arguments
    else :
        def decorator(f) :
            def wrapped(*args,**kwargs):
                if not check_r():
                    raise RscriptExecutableNotFound('Rscript executable could not be '
                            'found on PATH. Rscript is needed for this functionality')
                else :
                    require_r_package('jsonlite')
                    for pkg in pkgs :
                        require_r_package(pkg)
                return f(*args,**kwargs)
            return wrapped
    return decorator

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
out.fn <- args[4]; metadata.out.fn <- args[5]; params.out.fn <- args[6];
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

    .. note::
        The attributes are only populated after the execute() method has
        been run

    Parameters
    ----------

    rscript_path : str
        path to the R script to run

    counts : pandas.DataFrame, optional
        dataframe containing counts to be passed to R

    metadata : pandas.DataFrame, optional
        dataframe containing metadata to be passed to R

    params : dict, optional
        dict of parameters to be passed to R

    output_fn : str, optional
        path to file where R should write output, if not provided the output
        is written to a temporary file and deleted upon WrapR object deletion

    metadata_out_fn : str, optional
        path to file where R should write metadata output

    rpath : str
        path to the Rscript executable, taken from the PATH environment
        variable if None

    raise_on_error : bool
        raise an exception if R encounters an error, other wise fail silently
        and deadly

    Attributes
    ----------

    output : pandas.DataFrame
        dataframe of the tabular output created by R script

    metadata_out : pandas.DataFrame
        dataframe of the tabular metadata output created by R script

    params_out : dict
        dict of the output parameters list created by R script

    stdout : str
        string capturing the standard output of the R script

    stderr : str
        string capturing the standard error of the R script

    retcode : int
        return code of the R process

    success : bool
        True if retcode == 0

    Raises
    ------

    de_toolkit.wrapr.RExecutionError
        when *raise_on_error* is True, raise whenever R encounters an error

    Examples
    --------

    Basic usage accepts a path to an R script and loads the content of
    the file pointed to by *out.fn* in the R script into the *output*
    attribute:

    >>> with open('script.R','wt') as f :
            # note reference to implicitly defined *out.fn*
            # R variable
            f.write('write.csv(c(1,2,3,4),out.fn)')
    >>> r = WrapR('script.R',output_fn='test.csv')
    >>> r.execute()
    >>> r.output
       x
    1  1
    2  2
    3  3
    4  4
    >>> pandas.read_csv('test.csv',index_col=0)
       x
    1  1
    2  2
    3  3
    4  4

    Can also use a context manager when the output doesn't need to be
    written to a named file:

    >>> with WrapR('script.R') as r :
            r.execute()
            print(r.output)
       x
    1  1
    2  2
    3  3
    4  4

    The standard output of the R script can be accessed with the *stdout*
    attribute:

        >>> with open('euler.R','wt') as f :
                f.write('exp(complex(real=0,imag=pi))+1')
        >>> with WrapR('euler.R','wt') as r :
                r.execute()
                print(r.stdout)
        [1] 0+1.224647e-16i


    '''

    def __init__(self,
            rscript_path,
            counts=None,
            metadata=None,
            params=None,
            output_fn=None,
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
        self._paths['output'] = output_fn
        if output_fn is None :
            self._files['output'] = NamedTemporaryFile('wt',delete=False)
            self._paths['output'] = self._files['output'].name

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
        self.output = None
        self.metadata_out = None
        self.params_out = None

        self.raise_on_error = raise_on_error

    @require_r
    def execute(self) :
        '''
        Execute the R script and load in the resulting output files, if any.
        '''

        # construct Rscript command
        cmd = ('{rpath} --vanilla {rscript} {counts_in} {meta_in} {params_in} '
               '{output} {meta_out} {params_out}').format(
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
        if os.path.exists(self._paths['output']) :
            try :
                self.output = pd.read_csv(
                    self._paths['output'],
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

    Parameters
    ----------

    Rcode : str
        string containing valid R code to be executed

    Returns
    -------

    obj
        A WrapR object executed with the code in input string

    Examples
    --------

    >>> with wrapr('write.csv(c(1,2,3,4),out.fn)') as r :
            print(r.output)
       x
    1  1
    2  2
    3  3
    4  4

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

    if args['run'] :

        counts_obj = CountMatrixFile(
              args['<counts_in>'],
              args['--meta-in'],
              strict=args.get('--strict',False)
        )

        params = None
        if os.path.exists(args['--params-in']) :
            with open(args['--params-in'],'rt') as f :
                params = json.load(f)

        with WrapR(
            args['<rscript>'],
            counts_obj.counts,
            counts_obj.column_data,
            params=params,
            output_fn=args['<out>'],
            metadata_out_fn=args['--meta-out'],
            params_out_fn=args['--params-out'],
            rpath=args['--rpath']
            ) as wr :
            wr.execute()

    elif args['check'] :

        r = check_r()
        print('R found:',r,file=sys.stderr)

        if not r :
            raise RscriptExecutableNotFound(
                    'Rscript executable not found, wrapr interface and '
                    'functions will not work'
            )

        print('R path: {}'.format(get_r_path()),file=sys.stderr)

        jsonlite = check_r_package('jsonlite')
        print('jsonlite found:',jsonlite,file=sys.stderr)

        if not jsonlite :
            raise RPackageMissing('ERROR: R package jsonlite must be installed, '
                  'wrapr interface and functions will not work'
            )


if __name__ == '__main__' :

  main()
