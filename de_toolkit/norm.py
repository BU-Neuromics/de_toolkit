import sys
import numpy as np

class NormalizationException(Exception) : pass

# DESeq2 v1.3.34 uses this R code for normalization
#estimateSizeFactorsForMatrix <- function( counts, locfunc = median, geoMeans )
#{
#  if (missing(geoMeans)) {
#    loggeomeans <- rowMeans(log(counts))
#  } else {
#    if (length(geoMeans) != nrow(counts)) {
#      stop("geoMeans should be as long as the number of rows of counts")
#    }
#    loggeomeans <- log(geoMeans)
#  }
#  if (all(is.infinite(loggeomeans))) {
#    stop("every gene contains at least one zero, cannot compute log geometric means")
#  }
#  apply(counts, 2, function(cnts) {
#    exp(locfunc((log(cnts) - loggeomeans)[is.finite(loggeomeans) & cnts > 0]))
#  })
#}

def estimateSizeFactors(cnts) :

  loggeomeans = np.log(cnts).mean(axis=1)
  if all(~np.isfinite(loggeomeans)) :
    raise NormalizationException(
     "every gene contains at least one zero, cannot compute log geometric means"
    )

  divFact = np.log(cnts).sub(loggeomeans,axis='index')
  sizeFactors = np.exp(divFact.apply(lambda c: c[np.isfinite(c)].median()))

  norm_cnts = cnts.div(sizeFactors,axis='columns')

  return sizeFactors, norm_cnts


def deseq2(count_mat) :
  pass

def trimmed_mean(count_mat) :
  pass

def reference(count_mat,reference) :
  pass

def library_size(count_mat,sizes=None) :
  pass

def fpkm(count_mat,annotation) :
  pass

def custom_norm(count_mat,factors) :
  pass
