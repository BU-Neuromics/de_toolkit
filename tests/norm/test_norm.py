import docopt
import numpy as np
import pytest
from de_toolkit.norm import main

def test_norm_cli():
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_deseq2_norm_cli(fake_counts_csv,fake_column_data_csv):
  main(['deseq2',fake_counts_csv])

def test_estimateSizeFactors(fake_counts_numpy_matrix) :

  from de_toolkit.norm import estimateSizeFactors

  # the matrix is constructed such that the size factors are
  # 1/4, 1, 4
  # the geometric mean of each row is the middle sample
  cnts = np.array([
    [2.0,4.0,8.0]
    ,[3.0,9.0,27.0]
    ,[4.0,16.0,64.0]
    ,[5.0,25.0,125.0]
    ,[6.0,36.0,216.0]
  ])

  cnts = fake_counts_numpy_matrix

  true_size_factors = cnts[2,:]/cnts[2,1]

  size_factors = estimateSizeFactors(cnts)

  assert np.allclose(size_factors, true_size_factors)

def test_estimateSizeFactors_allzero(fake_counts_numpy_matrix) :
  # make sure the function raises when all rows contain one zero
  from de_toolkit.norm import estimateSizeFactors, NormalizationException

  # set the first column to zero
  cnts[:,0] = 0

  with pytest.raises(NormalizationException) :
    estimateSizeFactors(cnts)

def test_estimateSizeFactors_somezero() :

  from de_toolkit.norm import estimateSizeFactors

  # the matrix is constructed such that the size factors are
  # 1/4, 1, 4
  # the geometric mean of each row is the middle sample
  cnts = np.array([
    [2.0,4.0,8.0,0]
    ,[3.0,9.0,27.0,81.0]
    ,[4.0,16.0,64.0,256.0] # <- this is the median normalized factor
    ,[5.0,25.0,125.0,625.0]
    ,[6.0,36.0,216.0,0]
  ])

  geom_mean = cnts[2,:].prod()**(1/4)

  true_size_factors = cnts[2,:]/geom_mean

  size_factors = estimateSizeFactors(cnts)
  assert np.allclose(size_factors, true_size_factors)


def test_deseq2() :

  from de_toolkit import CountMatrix
  from de_toolkit.norm import deseq2

  cnts = np.array([
    [2.0,4.0,8.0]
    ,[3.0,9.0,27.0]
    ,[4.0,16.0,64.0]
    ,[5.0,25.0,125.0]
    ,[6.0,36.0,216.0]
  ])

  true_size_factors = cnts[2,:]/cnts[2,1]

  true_norm_cnts = cnts/true_size_factors

  norm_cnts = deseq2(cnts)

  assert np.allclose(norm_cnts, true_norm_cnts)

def test_library_size() :

  from de_toolkit.norm import library_size

  cnts = np.array([
    [1.0, 2.0, 3.0]
    ,[1.0, 2.0, 3.0]
    ,[1.0, 2.0, 3.0]
  ])

  true_norm_cnts = np.array([
    [1/3, 1/3, 1/3]
    ,[1/3, 1/3, 1/3]
    ,[1/3, 1/3, 1/3]
  ])

  norm_cnts = library_size(cnts)

  assert np.allclose(norm_cnts, true_norm_cnts)
