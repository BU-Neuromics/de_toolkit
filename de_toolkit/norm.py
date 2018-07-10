'''
Usage:
    detk-norm deseq2 <counts_fn> [options]
    detk-norm trimmed_mean <counts_fn>
    detk-norm library <counts_fn>
    detk-norm fpkm <counts_fn> <gtf>
    detk-norm custom <counts_fn>

Options:
    -o FILE --output=FILE        Destination of primary output [default: stdout]

'''
from docopt import docopt
import sys
import numpy as np
import pandas
from .common import CountMatrixFile
from .util import stub
from .wrapr import require_r, wrapr

class NormalizationException(Exception) : pass

# DESeq2 v1.14.1 uses this R code for normalization
#function (counts, locfunc = stats::median, geoMeans, controlGenes) 
#{
#        if (missing(geoMeans)) {
#                loggeomeans <- rowMeans(log(counts))
#        }
#        else {
#                if (length(geoMeans) != nrow(counts)) {
#                        stop("geoMeans should be as long as the number of rows of counts")
#                }
#                loggeomeans <- log(geoMeans)
#        }
#        if (all(is.infinite(loggeomeans))) {
#                stop("every gene contains at least one zero, cannot compute log geometric means")
#        }
#        sf <- if (missing(controlGenes)) {
#                apply(counts, 2, function(cnts) {
#                        exp(locfunc((log(cnts) - loggeomeans)[is.finite(loggeomeans) & 
#                                cnts > 0]))
#                })
#        }
#        else {
#                if (!(is.numeric(controlGenes) | is.logical(controlGenes))) {
#                        stop("controlGenes should be either a numeric or logical vector")
#                }
#                loggeomeansSub <- loggeomeans[controlGenes]
#                apply(counts[controlGenes, , drop = FALSE], 2, function(cnts) {
#                        exp(locfunc((log(cnts) - loggeomeansSub)[is.finite(loggeomeansSub) & 
#                                cnts > 0]))
#                })
#        }
#        sf
#}


def estimateSizeFactors(cnts) :

    loggeomeans = np.log(cnts).mean(axis=1)
    if all(~np.isfinite(loggeomeans)) :
        raise NormalizationException(
         'every gene contains at least one zero, cannot compute log geometric means'
        )

    divFact = (np.log(cnts).T - loggeomeans).T
    sizeFactors = np.exp(
        np.apply_along_axis(
            lambda c: np.median(c[np.isfinite(c)])
            ,0
            ,divFact
        )
    )

    return sizeFactors

@require_r('DESeq2')
def estimateSizeFactors_wrapr(cnts) :

    script = '''\
    library(DESeq2)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1))
    colData <- data.frame(name=seq(ncol(cnts)))
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = ~ 1)
    dds <- estimateSizeFactors(dds)
    write.csv(sizeFactors(dds),out.fn)
    '''

    with wrapr(script,
            counts=pandas.DataFrame(cnts),
            raise_on_error=False) as r :
        deseq2_size_factors = r.output['x'].values

    return list(deseq2_size_factors)

def deseq2(count_obj) :

    count_mat = count_obj.counts.values

    sizeFactors = estimateSizeFactors(count_mat)
    norm_cnts = count_mat/sizeFactors
    

    normalized = pandas.DataFrame(norm_cnts

        ,index=count_obj.counts.index

        ,columns=count_obj.counts.columns

    )
    return normalized

@require_r('DESeq2')
def deseq2_wrapr(count_obj) :

    script = '''\
    library(DESeq2)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1))
    colData <- read.csv(metadata.fn,row.names=1)
    str(params$design)
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = formula(params$design))
    dds <- estimateSizeFactors(dds)
    write.csv(counts(dds,normalized=TRUE),out.fn,row.names=TRUE)
    '''

    # we need to get rid of the counts from the left hand side and the Intercept
    # from the right, otherwise the model matrix is not full rank and DESeq2 whines
    count_obj.design_matrix.drop_from_lhs('counts')
    count_obj.design_matrix.drop_from_rhs('Intercept')

    with wrapr(script,
            counts=count_obj.counts,
            metadata=count_obj.design_matrix.full_matrix,
            params={'design':count_obj.design},
            raise_on_error=True) as r :
        norm_counts = r.output.values

    return norm_counts

@stub
def trimmed_mean(count_mat) :
    pass

def library_size(count_mat,sizes=None) :
    '''
    Divide each count by column sum
    '''
    return count_mat / np.sum(count_mat,axis=0)

@stub
def fpkm(count_mat,annotation) :
    pass

@stub
def custom_norm(count_mat,factors) :
    pass

def main(argv=None) :

    args = docopt(__doc__,argv=argv)

    count_obj = CountMatrixFile(args['<counts_fn>'])

    if '<cov_fn>' in args :
        count_obj.add_covariates(args['<cov_fn>'])

    if args['deseq2'] :
        count_obj.normalized['deseq2'] = deseq2(count_obj)
        fp = sys.stdout if args['--output']=='stdout' else args['--output']
        count_obj.normalized['deseq2'].to_csv(fp)
