'''
Usage:
  detk-norm deseq2 <counts_fn>
  detk-norm trimmed_mean <counts_fn>
  detk-norm library <counts_fn>
  detk-norm fpkm <counts_fn> <gtf>
  detk-norm custom <counts_fn>
'''
from docopt import docopt
import sys
import numpy as np
from .util import stub, load_count_mat_file

class NormalizationException(Exception) : pass

# DESeq2 v1.3.34 uses this R code for normalization
#estimateSizeFactorsForMatrix <- function( counts, locfunc = median, geoMeans )
#{
#  if (missing(geoMeans)) {
#    loggeomeans <- rowMeans(log(counts))
#  } else {
#    if (length(geoMeans) != nrow(counts)) {
#      stop('geoMeans should be as long as the number of rows of counts')
#    }
#    loggeomeans <- log(geoMeans)
#  }
#  if (all(is.infinite(loggeomeans))) {
#    stop('every gene contains at least one zero, cannot compute log geometric means')
#  }
#  apply(counts, 2, function(cnts) {
#    exp(locfunc((log(cnts) - loggeomeans)[is.finite(loggeomeans) & cnts > 0]))
#  })
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

def deseq2(count_mat) :

  sizeFactors = estimateSizeFactors(count_mat)
  norm_cnts = count_mat/sizeFactors

  return norm_cnts

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

def main() :

  args = docopt(__doc__)

  count_obj = load_count_mat_file(args['<count_fn>'])

  if '<cov_fn>' in args :
    count_obj.add_covariates(args['<cov_fn>'])

  if args['deseq2'] :
    deseq2(count_obj)
