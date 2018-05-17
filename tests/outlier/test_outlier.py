import docopt
import pytest
import warnings
import os


def test_entropy():

    '''
    Function acts as a unit test for the entropy outlier module.

    '''
    ## Generate fake count data ##
    # initialize a vector of zeros with length 20
    base = list([0] * 20)

    # initialize the test df
    test_df = pd.DataFrame()

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

    test_df.to_csv('test_entropy_counts.csv')

    ## Run unit test ##
    # run the test data through the program
    results = entropy_calc('test_entropy_counts.csv', 0.05)

    # cleanup the csv
    os.remove('test_entropy_counts.csv')

    # check the results of the unit test
    assert results['entropy'].iloc[19] == 0 and results['entropy_p0_05'].iloc[19] == True
    assert True not in results['entropy_p0_05'].iloc[0:18].values.tolist()
