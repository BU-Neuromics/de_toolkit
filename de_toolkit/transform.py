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

def shrink_outliers(count_mat) :
  pass

def trim_outliers(count_mat) :
  pass

def vst(count_mat) :
  pass

def ruvseq(count_mat) :
  pass

