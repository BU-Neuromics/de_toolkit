import docopt
import pytest
from de_toolkit.outlier import test
import warnings


def test_entropy_calc():

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
        colnames.append('feature_' + str(num))
    rownames = []
    for num in range(0,20):
        rownames.append('sample_' + str(num))

    test_df.columns = colnames
    test_df.index = rownames

    test_df.to_csv('test_counts.csv')


    ## Run unit test ##
    # run the test data through the program
    results = entropy_calc('test_counts.csv', 0.05)

    # check the results of the unit test
    assert results['entropy'].iloc[0] == 0 and results['p0_05'].iloc[0] == True
    assert True not in results['p0_05'].iloc[1:].values.tolist()
    assert threshold < results['entropy'].iloc[1] and threshold > results['entropy'].iloc[0]

    # if it passes, return 1
    return(1)


with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  test_entropy_calc()
