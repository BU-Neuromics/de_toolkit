'''
Usage:
  detk-norm deseq2 <counts_fn> [options]
  detk-norm trimmed_mean <counts_fn>
  detk-norm library <counts_fn>
  detk-norm fpkm <counts_fn> <gtf>
  detk-norm custom <counts_fn>

Options:
  -o FILE --output=FILE    Destination of primary output [default: stdout]

'''
from docopt import docopt
import sys
import numpy as np
import pandas
from .common import CountMatrixFile
from .util import stub, require_deseq2, pandas_to_rmatrix, pandas_to_rdataframe

class NormalizationException(Exception) : pass

# DESeq2 v1.14.1 uses this R code for normalization
#function (counts, locfunc = stats::median, geoMeans, controlGenes) 
#{
#    if (missing(geoMeans)) {
#        loggeomeans <- rowMeans(log(counts))
#    }
#    else {
#        if (length(geoMeans) != nrow(counts)) {
#            stop("geoMeans should be as long as the number of rows of counts")
#        }
#        loggeomeans <- log(geoMeans)
#    }
#    if (all(is.infinite(loggeomeans))) {
#        stop("every gene contains at least one zero, cannot compute log geometric means")
#    }
#    sf <- if (missing(controlGenes)) {
#        apply(counts, 2, function(cnts) {
#            exp(locfunc((log(cnts) - loggeomeans)[is.finite(loggeomeans) & 
#                cnts > 0]))
#        })
#    }
#    else {
#        if (!(is.numeric(controlGenes) | is.logical(controlGenes))) {
#            stop("controlGenes should be either a numeric or logical vector")
#        }
#        loggeomeansSub <- loggeomeans[controlGenes]
#        apply(counts[controlGenes, , drop = FALSE], 2, function(cnts) {
#            exp(locfunc((log(cnts) - loggeomeansSub)[is.finite(loggeomeansSub) & 
#                cnts > 0]))
#        })
#    }
#    sf
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

@require_deseq2
def estimateSizeFactors_rpy(cnts) :

  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr
  from rpy2.rinterface import RRuntimeError

  base = importr('base')

  deseq2 = importr('DESeq2')

  m = robjects.r.matrix(
    robjects.FloatVector(
      cnts.ravel()
    )
    ,nrow=cnts.shape[0]
    ,byrow=True
  )

  deseq2_size_factors = deseq2.estimateSizeFactorsForMatrix(m)

  return list(deseq2_size_factors)

def deseq2(count_obj) :

  count_mat = count_obj.counts.as_matrix()

  sizeFactors = estimateSizeFactors(count_mat)
  norm_cnts = count_mat/sizeFactors
  

  normalized = pandas.DataFrame(norm_cnts

    ,index=count_obj.counts.index

    ,columns=count_obj.counts.columns

  )
  return normalized

@require_deseq2
def deseq2_rpy(count_obj) :

  from rpy2 import robjects
  import rpy2.rlike.container as rlc
  from rpy2.robjects.packages import importr
  from rpy2.rinterface import RRuntimeError

  deseq2 = importr('DESeq2')

  cnts = pandas_to_rmatrix(count_obj.counts)

  colData = pandas_to_rdataframe(count_obj.column_data)

  dds = deseq2.DESeqDataSetFromMatrix(
    countData = cnts
    ,colData = colData
    ,design = robjects.Formula(count_obj.design if count_obj.design else '~')
  )
  dds = deseq2.estimateSizeFactors_DESeqDataSet(dds)

  norm_counts = deseq2.counts_DESeqDataSet(dds,normalized=True)

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
