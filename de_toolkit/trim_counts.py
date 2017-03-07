from math import sqrt
import sys
import pandas as pd

def pmf_transform(x,shrink_factor=0.25,max_p=None,iters=1000) :

  x = x.copy()
  max_p = max_p or sqrt(1./len(x))

  for i in range(iters) :
    p_x = x/x.sum()

    if x.sum() == 0 :
      print 'all samples set to zero, returning'
      break

    p_x_outliers = p_x>max_p

    if not any(p_x_outliers) :
      break # done

    max_non_outliers = max(x[~p_x_outliers])

    x[p_x_outliers] = max_non_outliers+(x[p_x_outliers]-max_non_outliers)*shrink_factor

  if i == iters :
    print 'PMF transform did not converge'
    print p_x
    print p_x_outliers

  return x


cnts = pd.read_csv("all_mRNA_nonzero_norm_counts.csv",index_col=0,header=0)
sizeFactors = pd.read_csv("all_mRNA_nonzero_norm_counts_sizeFactors.csv",
  index_col=0,names=('sizeFactor',))
# there are three extra lines from htseq-count
# H_0014 is a bad sample, omit it
#cnts = cnts.ix[:-3,[c for c in cnts.columns if c!='H_0014']]
sizeFactors = sizeFactors.sizeFactor[cnts.columns]

cn_cols = [c for c in cnts.columns if c.startswith('C')]
nd_cols = [c for c in cnts.columns if not c.startswith('C')]

nonzero_thresh_pass = (((cnts[cn_cols]==0).sum(axis=1)<len(cn_cols)/2.) |
                       ((cnts[nd_cols]==0).sum(axis=1)<len(nd_cols)/2.))

cnts = cnts[nonzero_thresh_pass]

trim_cnts = cnts.apply(pmf_transform,axis=1)
trim_cnts.to_csv("all_mRNA_nonzero_norm_counts_trim.csv")
trim_cnts.mul(sizeFactors,axis=1).apply(pd.Series.round).to_csv("all_mRNA_nonzero_raw_counts_trim.csv")
