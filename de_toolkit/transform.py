'''
Usage:
    detk-transform plog [options] <count_fn>
    detk-transform vst [options] <count_fn>
    detk-transform rlog [options] <count_fn> [<design> <cov_fn>]
'''
TODO = '''
    detk-transform ruvseq <count_fn>
'''

cmd_opts = {
    'vst':'''\
Usage:
    detk-transform vst [options] <count_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
''',
    'plog':'''\
Usage:
    detk-transform plog [options] <count_fn>

Options:
    -c N --pseudocount=N   The pseudocount to use when taking the log transform [default:1]
    -b B --base=B          The base of the log to use [default: 10]
    -o FILE --output=FILE  Destination of primary output [default: stdout]
''',
    'rlog':'''\
Usage:
    detk-transform rlog [options] <count_fn> [<design> <cov_fn>]

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
''',
}

from docopt import docopt
import math
import numpy
import pandas
import sys
from .common import CountMatrixFile
from .wrapr import (
                require_r, require_deseq2, wrapr, RExecutionError, RPackageMissing,
                require_r_package
        )
from .util import stub

def plog(count_obj,pseudocount=1,base=10) :
    '''
    Logarithmic transform of a counts matrix with fixed pseudocount, i.e. $\\log(x+c)$

    Parameters
    ----------
    count_obj : CountMatrix object
        count matrix object

    Returns
    -------
    pandas.DataFrame
        log transformed counts dataframe with the same dimensionality as input
        counts

    '''
    return numpy.log(count_obj.counts+pseudocount)/numpy.log(base)

@require_r('DESeq2','SummarizedExperiment')
def vst(count_obj) :
    '''
    Variance Stabilizing Transformation implemented in the DESeq2 bioconductor
    package.

    Parameters
    ----------
    count_obj : CountMatrix object
        count matrix object

    Returns
    -------
    pandas.DataFrame
        VST transformed counts dataframe with the same dimensionality as input
        counts
    '''

    script = '''\
    library(DESeq2)
    library(SummarizedExperiment)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1))
    colData <- data.frame(name=seq(ncol(cnts)))
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = ~ 1)
    dds <- varianceStabilizingTransformation(dds)
    write.csv(assay(dds),out.fn)
    '''

    with wrapr(script,
            counts=count_obj.counts,
            raise_on_error=True) as r :
        vsd_values = r.output

    return vsd_values

@require_r('DESeq2','SummarizedExperiment')
def rlog(count_obj,blind=True) :
    '''
    Regularized log (rlog) transformation implemented in the DESeq2 bioconductor
    package.

    Parameters
    ----------
    count_obj : CountMatrix object
        count matrix object
    blind : bool
        the `blind` parameter as passed to the `rlog` function in DESeq2. if
        False, `count_obj` is expected to have `column_data` and a valid
        design as required by the R function

    Returns
    -------
    pandas.DataFrame
        rlog transformed counts dataframe with the same dimensionality as input
        counts
    '''


    script = '''\
    library(DESeq2)
    library(SummarizedExperiment)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1))

    # load design matrix
    if(file.info(metadata.fn)$size != 0) {
        colData <- read.csv(metadata.fn,header=T,as.is=T,row.names=1)
    } else {
        # just to convince DESeq2 that everything is ok when we're doing a
        # blind rlog
        n.fake.class.1 <- floor(ncol(cnts)/2)
        fake.classes <- factor(c(
            rep(0,n.fake.class.1),
            rep(1,ncol(cnts)-n.fake.class.1))
        )
        colData <- data.frame(name=fake.classes)
    }

    blind <- params$blind
    form <- params$design

    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = formula(form)
    )

    dds <- rlog(dds,blind=blind)
    write.csv(assay(dds),out.fn)
    '''

    column_data = None
    if not blind and count_obj.column_data is not None :
        column_data = count_obj.design_matrix.full_matrix

    params = {
        'design': '~ 1' if blind else count_obj.design,
        'blind': blind
    }

    with wrapr(script,
            counts=count_obj.counts,
            metadata=column_data,
            params=params,
            raise_on_error=True) as r :
        vsd_values = r.output

    return vsd_values

@stub
def ruvseq(count_obj) :
    pass

def main(argv=sys.argv) :

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts) :
        docopt(__doc__)
    argv = argv[1:]
    cmd = argv[0]

    if cmd == 'vst' :
        args = docopt(cmd_opts['vst'],argv)
        count_obj = CountMatrixFile(args['<count_fn>'])

        out_df = vst(count_obj)

    if cmd == 'plog' :
        args = docopt(cmd_opts['plog'],argv)
        count_obj = CountMatrixFile(args['<count_fn>'])

        out_df = plog(count_obj)
    
    elif cmd == 'rlog' :
        args = docopt(cmd_opts['rlog'],argv)

        count_obj = CountMatrixFile(
            args['<count_fn>']
            ,args['<cov_fn>']
            ,design=args['<design>']
            ,strict=args.get('--strict',False)
        )

        out_df = rlog(count_obj)

    if args['--output'] == 'stdout' :
        f = sys.stdout
    else :
        f = args['--output']

    out_df.to_csv(f,sep='\t')

if __name__ == '__main__' :
    main()
