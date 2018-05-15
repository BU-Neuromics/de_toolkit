'''
Usage:
    detk-outlier entropy <counts_fn> [options]

Options:

    -p P --percentile=P
    -o FILE --output=FILE
    --plot-output=FILE

'''

import numpy as np
import pandas as pd
from docopt import docopt
import csv
import scipy.stats as sc
import matplotlib as plt
import matplotlib.pyplot as plt



def entropy_calc(file, pval, output, test=None):

    '''
    Function accepts a counts file, a cutoff threshold. The counts file should have the samples
    as the columns and the features as the rows. The cutoff threshold should be a float value
    between 0 and 1. This function will output a csv of the entropy values and threshold booleans,
    as well as a histogram plot of the features.

    '''

    if test == 'test':
        counts_transpose = file
    else:
        mat = file
        filetype = mat[-3:]

        # check for the type of file inputted
        if filetype == 'csv':
            counts = pd.read_csv(mat, sep=',', index_col=0)
        elif filtype == 'tsv':
            counts = pd.read_csv(mat, sep='\t', index_col=0)
        else:
            raise Exception('Unsupported filetype. Please use a csv or tsv counts file.')


        counts_transpose = counts.copy().transpose()

    threshold = pval
    trshld_name = str(threshold).split('.')[1]

    # check that no features have a total of zero
    all_features = counts_transpose.columns.tolist()
    counts_transpose = counts_transpose.loc[:, (counts_transpose != 0).any(axis=0)]
    nonzero_features = counts_transpose.columns.tolist()
    dropped_features = set(all_features) - set(nonzero_features)

    # create a null results df for all of the dropped features
    dropped_df = pd.DataFrame(columns=['entropy', 'p0_{}'.format(trshld_name)], index=dropped_features)
    dropped_df.replace(dropped_df, 'Null')

    # calculate the entropy over all of the features
    entropy = counts_transpose.apply(func=sc.entropy, axis=0)
    entropy = entropy.sort_values(ascending=True)

    # gathers the features and entropy values for the respective quantile groups
    entropy_threshold = np.percentile(entropy, q=threshold)

    # create the results of the entropy test
    # column 1 is the entropy value
    # column 2 is a boolean indication whether the value is under the user described threshold
    results_df = pd.DataFrame(entropy, columns=['entropy'])
    results_df['p0_{}'.format(trshld_name)] = entropy <= entropy_threshold
    frames = [results_df, dropped_df]
    results_df = pd.concat(frames)

    if test == 'test':
        return(results_df, entropy_threshold, trshld_name)
    else:
        output_csv = output + '_values.csv'
        output_plot = output + '_plot.png'

        # write the results to a csv
        results_df.to_csv(output_csv)

        # Entropy Histogram
        fig = plt.gcf()
        plt.hist(entropy, bins='auto', log=True)
        plt.axvline(entropy_threshold, color='red')
        plt.xlabel('Entropy')
        plt.ylabel('Samples Per Bin')
        plt.title('Binned Feature Entropy')
        plt.legend(['P < {}'.format(threshold), 'Data'])
        fig.set_size_inches(10,10)
        fig.savefig(output_plot,dpi=100)
        #plt.show()


## Test Cases ##
def test():

    '''
    Function acts as a unit test for the entropy outlier module.

    '''

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

    # run the test data through the program
    results, threshold, trshld_name = entropy_calc(test_df, 0.05, 'test', 'test')

    # check the results of the unit test
    assert results['entropy'].iloc[0] == 0 and results['p0_{}'.format(trshld_name)].iloc[0] == True
    assert True not in results['p0_{}'.format(trshld_name)].iloc[1:].values.tolist()
    assert threshold < results['entropy'].iloc[1] and threshold > results['entropy'].iloc[0]

    # if it passes, return 1
    return(1)


def main(argv=None):

    '''
    Function runs the unit test and the following entropy outlier module.

    '''

    args = docopt(__doc__, argv=argv)
    args['<counts_fn>'] = args.get('<counts_fn>')
    args['<perc>'] = args.get('<perc>')
    args['<out_fn>'] = args.get('<out_fn>')



    file = str(args['<counts_fn>'])
    pval = float(args['--percentile'])
    output = str(args['--output'])


    # run the test case
    test_pass = test()

    # check the unit test and run program if ok
    if test_pass == 1:
        entropy_calc(file, pval, output)
    else:
        raise Exception('Error: Unit test did not pass.')


if __name__ == '__main__':
    main()
