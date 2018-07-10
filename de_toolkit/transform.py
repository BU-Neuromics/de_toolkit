'''
Usage:
    detk-transform vst <counts_fn> <cov_fn>
    detk-transform ruvseq <counts_fn>
    detk-transform trim <counts_fn>
    detk-transform shrink <counts_fn>
'''
from docopt import docopt
from .common import CountMatrixFile
from .wrapr import (
                require_r, require_deseq2, wrapr, RExecutionError, RPackageMissing,
                require_r_package
        )
from .util import stub

def pmf_transform(x,shrink_factor=0.25,max_p=None,iters=1000) :

    x = x.copy()
    max_p = max_p or sqrt(1./len(x))

    for i in range(iters) :
        p_x = x/x.sum()

        if x.sum() == 0 :
            print('all samples set to zero, returning')
            break

        p_x_outliers = p_x>max_p

        if not any(p_x_outliers) :
            break # done

        max_non_outliers = max(x[~p_x_outliers])

        x[p_x_outliers] = max_non_outliers+(x[p_x_outliers]-max_non_outliers)*shrink_factor

    if i == iters :
        print('PMF transform did not converge')
        print(p_x)
        print(p_x_outliers)

    return x

@stub
def shrink_outliers(count_obj) :
    pass

@stub
def trim_outliers(count_obj) :
    pass

@require_r('DESeq2','SummarizedExperiment')
def vst(count_obj) :

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
        vsd_values = r.output.values

    return vsd_values

@stub
def ruvseq(count_obj) :
    pass

def main(argv=None) :

    args = docopt(__doc__,argv=argv)

    count_obj = CountMatrixFile(
        args['<counts_fn>']
        ,column_data_f=args['<cov_fn>']
    )

    if args['vst'] :
        vst_counts = vst(count_obj)

    elif args['ruvseq'] :
        ruvseq(count_obj)
    elif args['trim'] :
        trim_outliers(count_obj)
    elif args['shrink'] :
        shrink_outliers(count_obj)

if __name__ == '__main__' :
    main()
