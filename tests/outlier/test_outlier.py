import pandas
import pytest
import warnings

def test_shrink(fake_counts_obj):
    from de_toolkit.outlier import shrink

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shrink(fake_counts_obj)
    #TODO need *actual* tests

def test_shrink_cli(fake_counts_csv):
    from de_toolkit.outlier import main

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(['detk-outlier','shrink',fake_counts_csv])
    #TODO need *actual* tests

'''
def test_transform_trim(fake_counts_obj):
    from de_toolkit.transform import trim

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        trim(fake_counts_obj)

def test_transform_trim_cli(fake_counts_csv):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(['detk-outlier','trim',fake_counts_csv])
'''

@pytest.fixture
def entropy_test_counts_obj(request) :
    from de_toolkit.common import CountMatrix
    ## Generate fake count data ##
    # initialize a vector of zeros with length 20
    base = list([0] * 20)

    # initialize the test df
    test_df = pandas.DataFrame()

    # loop through and incrememnt the base vector
    for num in range(0,20):
        base[num] = 1
        test_df[num] = base

    colnames = []
    for num in range(0,20):
        colnames.append('sample_' + str(num))
    rownames = []
    for num in range(0,20):
        rownames.append('feature_' + str(num))

    test_df.columns = colnames
    test_df.index = rownames

    ## Run unit test ##
    # run the test data through the program
    return CountMatrix(test_df)

def test_entropy(entropy_test_counts_obj):

    from de_toolkit.outlier import entropy

    results = entropy(entropy_test_counts_obj, 0.05)

    # check the results of the unit test
    assert results['entropy'].iloc[19] == 0 and results['entropy_p0_05'].iloc[19]
    assert True not in results['entropy_p0_05'].iloc[0:18].values.tolist()
