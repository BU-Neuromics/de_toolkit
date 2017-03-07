def filter_nonzero(count_mat,n=0.5,groups=None) :
  '''
  Filter rows from *count_mat* based on the number of zero counts.

  * if 0 < *n* < 1, then *n* is the fraction of samples that must be non-zero
  * if 1 <= *n* < *count_mat.shape[1]*, then *n* is the number of samples that
    must be non-zero
  * if *groups* is not *None*, it must be a list of column indices or names of
    samples that should be considered a group, and n is applied to each
     group separately. Rows are filtered if all groups fail the criterion based
     on *n*
  '''
  pass
