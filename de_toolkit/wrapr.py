'''
Usage: detk-wrapr [options] <rscript> <counts_in> <counts_out>
       [--meta-in=<metadata_in>]  [--meta-out=<metadata_out>]
       [--params-in=<params_in>] [--params-out=<params_out>]

Options:
    --rpath=PATH     Path to Rscript executable, inferred from the environment
                     by default
'''
from collections import defaultdict
import os
import pandas as pd
import subprocess
from tempfile import NamedTemporaryFile
from .common import CountMatrixFile
from .util import which

class RscriptExecutableNotFound(Exception) : pass

def get_r_path():
    return which('Rscript')

def check_r() :
    return get_r_path() is not None

def require_r(f):
    if not check_r():
        raise RscriptExecutableNotFound('Rscript executable could not be found '
                'on PATH. Rscript is needed for this functionality')

class WrapR(object) :
    def __init__(self,
            rscript_path,
            counts,
            metadata=None,
            params=None,
            counts_out_fn=None,
            metadata_out_fn=None,
            params_out_fn=None,
            rpath=None
            ) :

        self._files = {}
        self._paths = defaultdict(str)

        # custom rpath
        self._paths['rpath'] = get_r_path() if rpath is None else rpath

        # find real path to Rscript executable
        self._paths['rscript'] = os.path.realpath(rscript_path)

        # write counts to tempfile
        self._files['counts_in'] = NamedTemporaryFile(delete=False)
        self._paths['counts_in'] = self._files['counts_in'].name
        counts.to_csv(self._files['counts_in'])

        # set counts output file if provided, otherwise create temp file
        self._paths['counts_out'] = counts_out_fn
        if counts_out_fn is None :
            self._files['counts_out'] = NamedTemporaryFile(delete=False)
            self._paths['counts_out'] = self._files['counts_out'].name

        # write metadata to tempfile if provided
        self._files['meta_in'] = NamedTemporaryFile(delete=False)
        self._paths['meta_in'] = self._files['meta_in'].name
        if metadata is not None :
            metadata.to_csv(self._files['meta_in'])

        # set metadata output file if provided, otherwise create temp file
        self._paths['meta_out'] = metadata_out_fn
        if metadata_out_fn is None :
            self._files['meta_out'] = NamedTemporaryFile(delete=False)
            self._paths['meta_out'] = self._files['meta_out'].name

        # write out params json if provided
        self._files['params_in'] = NamedTemporaryFile(delete=False)
        self._paths['params_in'] = self._files['params_in'].name
        if params is not None :
            json.dump(params,self._files['params_in'])

        # initialize output members
        self.counts_out = None
        self.metadata_out = None
        self.params_out = None

    @require_r
    def execute(self) :

        # construct Rscript command
        cmd = ('{rpath} {rscript} {counts_in} {meta_in} {params_in} '
               '{counts_out} {meta_out} {params_out}').format(
                    **self._paths
               )

        # run the R script
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # raise if there was an error I guess
        p.check_returncode()

        # read in the outputs
        if os.path.exists(self._paths['counts_out']) :
            self.counts_out = pd.read_csv(self._paths['counts_out'])

        if os.path.exists(self._paths['meta_out']) :
            self.metadata_out = pd.read_csv(self._paths['meta_out'])

        if os.path.exists(self._paths['params_out']) :
            with open(self._paths['params_out'],'rt') as f :
                self.params_out = json.load(f)

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

    wr = WrapR(
        args['<rscript>'],
        counts_obj.counts,
        counts_obj.column_data,
        params=params,
        counts_out_fn=args['<counts_out>'],
        metadata_out_fn=args['<metadata_out>'],
        params_out_fn=args['<params_out>'],
        rpath=args['--rpath']
    )

    wr.execute()

if __name__ == '__main__' :

  main()
