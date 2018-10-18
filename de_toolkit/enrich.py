'''
Usage:
    detk-enrich fgsea [options] <gmt_fn> <result_fn>
Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
'''

todo = '''\
    detk-enrich fisher [options] <gmt_fn> <result_fn>
'''
cmd_opts = {
        'fgsea':'''\
Perform preranked Gene Set Enrichment Analysis using the fgsea bioconductor
package on the given gmt gene set file.

Usage:
    detk-enrich fgsea [options] <gmt_fn> <result_fn>

Options:
    -h --help                 Print out this help
    -o FILE --output=FILE     Destination of fgsea output [default: stdout]
    -p PROCS --cores=PROCS    Ask BiocParallel to use PROCS processes when
                              executing fgsea in parallel, requires the
                              BiocParallel package to be installed
    -i FIELD --idcol=FIELD    Column name or 0-based integer index to use as
                              the gene identifier [default: 0]
    -c FIELD --statcol=FIELD  Column name or 0-based integer index to use as
                              the statistic for ranking, defaults to the last
                              numeric column in the file
    -d --descending           Sort column descending, default is to sort
                              ascending, use this if you are sorting by p-value
    --abs                     Take the absolute value of the column before
                              passing to fgsea
    --minSize=INT             minSize argument to fgsea [default: 15]
    --maxSize=INT             maxSize argument to fgsea [default: 500]
    --nperm=INT               nperm argument to fgsea [default: 10000]
    --rda=FILE                write out the fgsea result to the provide file
                              using saveRDS() in R
''',
}
from collections import namedtuple, OrderedDict
import csv
from docopt import docopt
import sys
import numpy as np
import os
import pandas
import tempfile
from .common import CountMatrixFile
from .util import stub
from .wrapr import require_r, wrapr, require_r_package, RPackageMissing

GeneSet = namedtuple('GeneSet',('name','desc','ids'))
class GMT(OrderedDict):
    def __init__(self,sets={}) :
        super(GMT, self).__init__(self)
        for name,ids in sets.items() :
            self[name] = ids

    def __setitem__(self,name,ids) :
        self.add(name,ids)

    def add(self,name,ids,desc=None) :
        OrderedDict.__setitem__(
                self,
                name,
                GeneSet(name,desc or name,ids)
            )

    def load_file(self,fn) :
        self.fn = fn
        with open(fn) as f :
            for r in csv.reader(f,delimiter='\t') :
                self[r[0]] = [_.strip() for _ in r[2:]]

    def write_file(self,out_fn) :
        with open(out_fn,'wt') as f :
            out_f = csv.writer(f,delimiter='\t')
            for k,v in self.items() :
                out_f.writerow([k,k]+list(v.ids))

@require_r('fgsea')
def fgsea(
        gmt,
        stat,
        minSize=15,
        maxSize=500,
        nperm=10000,
        nproc=None,
        rda_fn=None) :

    script = '''\
    library(fgsea)
    library(data.table)

    ranks <- setNames(params$stat,params$id)
    pathways <- gmtPathways(params$gmt.fn)

    fgseaRes <- fgsea(
        pathways,
        ranks,
        minSize=params$minSize,
        maxSize=params$maxSize,
        nperm=params$nperm,
        nproc=params$nproc
    )
    if(!is.null(params$rda.fn)) {
        saveRDS(
            list(
                fgseaRes=fgseaRes,
                pathways=pathways,
                ranks=ranks,
                params=params
            ),
            file=params$rda.fn
        )
    }
    fwrite(fgseaRes,file=out.fn,sep=",",sep2=c("", " ", ""))
    '''

    # need to write out the gmt to file
    with tempfile.NamedTemporaryFile() as f :
        gmt.write_file(f.name)
        params = {
            'gmt.fn': os.path.realpath(f.name),
            'stat': stat.tolist(),
            'id': stat.index.tolist(),
            'minSize': minSize,
            'maxSize': maxSize,
            'nperm': nperm,
            'rda.fn': rda_fn,
            'nproc': nproc or 0
        }
        with wrapr(script,
                params=params,
                raise_on_error=True) as r :
            gsea_res = r.output

    return gsea_res

def main(argv=sys.argv) :

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts) :
        docopt(__doc__)
    argv = argv[1:]
    cmd = argv[0]

    if cmd == 'fgsea' :
        args = docopt(cmd_opts['fgsea'],argv)
        gmt = GMT()
        gmt.load_file(args['<gmt_fn>'])
        res_df = pandas.read_csv(
                args['<result_fn>'],
                sep=None,
                engine='python'
        )

        # first check if BiocParallel is available if --cores supplied
        cores = args['--cores']
        if cores is not None :
            cores = int(cores)

        def get_col_or_idcol(res_df,col) :
            if col not in res_df.columns :
                col = int(col)
                if col >= len(res_df.columns) :
                    raise ValueError()
                col = res_df.columns[col]
            return col

        col = args['--statcol']
        if col is not None :
            # check that the provided column is either in the column names
            # of the results df, or else is a valid integer index into it
                try :
                    col = get_col_or_idcol(res_df,col)
                except ValueError :
                    raise Exception((
                        'Stat column {} could not be found in results result '
                        'or interpreted as an integer index, aborting'
                        ).format(col)
                    )
        else :
            # pick the last numeric column
            col = res_df.columns[res_df.dtypes.apply(lambda x: np.issubdtype(x,np.number))][-1]

        stat = res_df[col]
        if args['--abs'] :
            stat = stat.abs()

        idcol = args['--idcol']
        if idcol is not None :
            try :
                idcol = get_col_or_idcol(res_df,idcol)
            except ValueError :
                raise Exception((
                    'ID column {} could not be found in results result '
                    'or interpreted as an integer index, aborting'
                    ).format(col)
                )

            stat.index = res_df[idcol]

        if args['--descending'] :
            stat = -stat

        out_df = fgsea(
                gmt,
                stat,
                minSize=int(args['--minSize']),
                maxSize=int(args['--maxSize']),
                nperm=int(args['--nperm']),
                nproc=cores,
                rda_fn=args['--rda']
            )

    fp = sys.stdout if args['--output']=='stdout' else args['--output']
    out_df.to_csv(fp)


