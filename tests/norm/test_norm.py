import docopt
import numpy as np
import os
import pandas
import pytest
import tempfile
import warnings
from de_toolkit import wrapr

# decorator for skipping if Rscript is not installed
r_test = pytest.mark.skipif(
        not wrapr.check_r(),
        reason='Rscript executable not found, skipping test'
)
deseq2_test = pytest.mark.skipif(
        not wrapr.check_r_package('DESeq2'),
        reason='DESeq2 R package not found, skipping test'
)

def test_norm_cli():
    from de_toolkit.norm import main
    with pytest.raises(docopt.DocoptExit) :
        main()

def test_deseq2_norm_cli(fake_counts_csv,fake_column_data_csv):
    from de_toolkit.norm import main
    main(['detk-norm','deseq2',fake_counts_csv])

def test_deseq2_norm_cli(fake_counts_csv,fake_column_data_csv):

    from de_toolkit import CountMatrixFile
    from de_toolkit.norm import main, deseq2

    f = tempfile.NamedTemporaryFile('wt',delete=False)
    f.close() # close the file so the command can write to it cross-platform

    main(['detk-norm','deseq2','--output={}'.format(f.name),fake_counts_csv])

    in_counts = CountMatrixFile(fake_counts_csv)
    norm_counts = deseq2(in_counts)

    out_counts = CountMatrixFile(f.name)

    assert np.allclose(norm_counts,out_counts.counts)

    # cleanup the csv
    os.remove(f.name)

@deseq2_test
def test_estimateSizeFactors(fake_counts_numpy_matrix) :

    from de_toolkit.norm import estimateSizeFactors, estimateSizeFactors_wrapr

    # the matrix is constructed such that the size factors are
    # 1/4, 1, 4
    # the geometric mean of each row is the middle sample
    cnts = fake_counts_numpy_matrix

    true_size_factors = cnts[2,:]/cnts[2,1]
    deseq2_size_factors = estimateSizeFactors_wrapr(cnts)
    size_factors = estimateSizeFactors(cnts)

    assert np.allclose(size_factors, true_size_factors)
    assert np.allclose(size_factors, deseq2_size_factors)

def test_estimateSizeFactors_allzero(fake_counts_numpy_matrix) :
    # make sure the function raises when all rows contain one zero
    from de_toolkit.norm import estimateSizeFactors, NormalizationException

    # set the first column to zero
    cnts = fake_counts_numpy_matrix.copy()
    cnts[:,0] = 0

    # this will raise warnings that we can safely ignore (I think)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(NormalizationException) :
            estimateSizeFactors(cnts)

@deseq2_test
def test_estimateSizeFactors_somezero(fake_counts_numpy_matrix) :

    from de_toolkit.norm import estimateSizeFactors, estimateSizeFactors_wrapr

    # the matrix is constructed such that the size factors are
    # 1/4, 1, 4
    # the geometric mean of each row is the middle sample
    cnts = fake_counts_numpy_matrix.copy()
    cnts[0,2] = cnts[4,2] = 0

    # the is the median normalized factor is in cnts[2,:]

    geom_mean = cnts[2,:].prod()**(1/cnts.shape[1])

    # this will raise warnings that we can safely ignore (I think)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        true_size_factors = cnts[2,:]/geom_mean
        deseq2_size_factors = estimateSizeFactors_wrapr(cnts)
        size_factors = estimateSizeFactors(cnts)

    assert np.allclose(size_factors, true_size_factors)
    assert np.allclose(size_factors, deseq2_size_factors)

def test_deseq2(fake_counts_obj) :

    from de_toolkit.norm import deseq2

    cnts = fake_counts_obj.counts.values

    true_size_factors = cnts[2,:]/cnts[2,1]

    true_norm_cnts = cnts/true_size_factors

    norm_cnts = deseq2(fake_counts_obj)

    assert np.allclose(norm_cnts, true_norm_cnts)

@deseq2_test
def test_deseq2_py_vs_wrapr(fake_counts_obj) :

    from de_toolkit.norm import deseq2, deseq2_wrapr

    # this raises R warnings about converting floats to integers that we can
    # ignore
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')

        # the design associated with fake_counts_obj is category ~ counts
        # which is intended for testing Firth
        # change it to something DESeq2 expects
        fake_counts_obj.design = 'counts ~ cont_cov + category'

        rpy_norm_counts = deseq2_wrapr(fake_counts_obj)

    py_norm_counts = deseq2(fake_counts_obj)

    assert np.allclose(rpy_norm_counts,py_norm_counts)

@deseq2_test
def test_deseq2_py_vs_wrapr_somezero(fake_counts_obj) :

    from de_toolkit.norm import deseq2, deseq2_wrapr

    fake_counts_obj.counts.iloc[0,2] = 0
    fake_counts_obj.counts.iloc[4,2] = 0

    # this raises R warnings about converting floats to integers that we can
    # ignore
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # the design associated with fake_counts_obj is category ~ counts
        # which is intended for testing Firth
        # change it to something DESeq2 expects
        fake_counts_obj.design = 'counts ~ cont_cov + category'

        rpy_norm_counts = deseq2_wrapr(fake_counts_obj)

        # suppress divide by zero warnings
        py_norm_counts = deseq2(fake_counts_obj)

    assert np.allclose(rpy_norm_counts,py_norm_counts)

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

def test_fpkm_missing_lens(fake_counts_obj,fake_counts_gene_lengths) :
    from de_toolkit.norm import fpkm, NormalizationException

    with pytest.raises(NormalizationException) :
        fpkm(
            fake_counts_obj.counts,
            pandas.Series([1,2,3],index=('gene1','gene2','gene3'))
        )

def test_fpkm(fake_counts_obj,fake_counts_gene_lengths) :
    from de_toolkit.norm import fpkm, NormalizationException

    res = fpkm(fake_counts_obj.counts, fake_counts_gene_lengths)
    assert np.allclose(res['a'],[1e-6]*res.shape[0])
    assert np.allclose(res['b'],list(np.arange(2,res.shape[0]+2)/1e6))
    assert np.allclose(res['c'],list(np.arange(2,res.shape[0]+2)**2/1e6))


