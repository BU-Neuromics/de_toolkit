import sys
import numpy as np
import pandas as pd

nonzero_counts = pd.read_csv('all_mRNA_nonzero_raw_counts.csv',index_col=0)

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
    sys.exit("every gene contains at least one zero, cannot compute log geometric means")

  divFact = np.log(cnts).sub(loggeomeans,axis='index')
  sizeFactors = np.exp(divFact.apply(lambda c: c[np.isfinite(c)].median()))

  norm_cnts = cnts.div(sizeFactors,axis='columns')

  return sizeFactors, norm_cnts

norm_size_factors, norm_cnts = estimateSizeFactors(nonzero_counts)
norm_size_factors.to_csv('all_mRNA_nonzero_norm_counts_sizeFactors.csv',index_label='ENSG')
norm_cnts.to_csv('all_mRNA_nonzero_norm_counts.csv',index_label='ENSG')

# below is just C and H
#nonzero_counts = nonzero_counts[[c for c in nonzero_counts.columns if not c.startswith('P')]]
#norm_size_factors, norm_cnts = estimateSizeFactors(nonzero_counts)
#norm_cnts.to_csv('C_H_mRNA_nonzero_norm_counts.csv',index_label='ENSG')

#nonzero_pseudo_counts = nonzero_counts.add(0.01*nonzero_counts.mean(axis=1),axis='index') 
#norm_size_factors_pseudo, norm_cnts_pseudo = estimateSizeFactors(nonzero_pseudo_counts)
#norm_cnts_pseudo.to_csv('C_H_mRNA_nonzero_norm_pseudo_counts.csv',index_label='ENSG')

#numzero = (nonzero_counts==0).sum(axis=1)
#numzero_p = [1.*(numzero>i).sum()/(numzero>0).sum() for i in range(numzero.max())]
