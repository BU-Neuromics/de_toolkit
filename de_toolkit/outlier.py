'''
Usage:
    detk-outlier entropy <counts_fn> [options]

Options:

    -p P --percentile=P    Float value between 0 and 1
    -o FILE --output=FILE  Name of the ouput csv
    --plot-output=FILE     Name of the plot png

'''

import numpy as np
import pandas as pd
from docopt import docopt
import csv
import scipy.stats as sc
import matplotlib as plt
import matplotlib.pyplot as plt
from .common import CountMatrixFile
import sys


def entropy_calc(file, pval, obj=None):

    '''
    Function accepts a counts file, a cutoff threshold. The counts file should have the samples
    as the columns and the features as the rows. The cutoff threshold should be a float value
    between 0 and 1. This function will output a csv of the entropy values and threshold booleans,
    as well as a histogram plot of the features.

    '''

    # if obj is none, this infers that a user is running the api
    if obj == None:
        mat = file
        counts = pd.read_csv(mat, sep=None, engine='python', index_col=0)
    elif obj == 'terminal':
        counts = pd.DataFrame(file)

    counts_transpose = counts.copy().transpose()

    threshold = pval
    trshld_name = str(threshold).split('.')[1]

    # check that no features have a total of zero
    all_features = counts_transpose.columns.tolist()
    counts_transpose = counts_transpose.loc[:, (counts_transpose != 0).any(axis=0)]
    nonzero_features = counts_transpose.columns.tolist()
    dropped_features = set(all_features) - set(nonzero_features)

    # create a null results df for all of the dropped features
    dropped_df = pd.DataFrame(columns=['entropy', 'entropy_p0_{}'.format(trshld_name)], index=dropped_features)
    dropped_df.replace(dropped_df, 'Null')

    # calculate the entropy over all of the features
    entropy = counts_transpose.apply(func=sc.entropy, axis=0)

    # gathers the features and entropy values for the respective quantile groups
    entropy_threshold = np.percentile(entropy, q=threshold)

    # create the results of the entropy test
    # column 1 is the entropy value
    # column 2 is a boolean indication whether the value is under the user described threshold
    results_df = pd.DataFrame(entropy, columns=['entropy'])
    results_df['entropy_p0_{}'.format(trshld_name)] = entropy < entropy_threshold
    frames = [results_df, dropped_df]
    results_df = pd.concat(frames)
    # set the results index to be in the same order as the counts index
    results_df.index = counts.index

    return(results_df)



def plot_entropy(file, pval, name=None, show=None, obj=None):

    '''
    Function accepts a counts file, a cutoff threshold. The counts file should have the samples
    as the columns and the features as the rows. The cutoff threshold should be a float value
    between 0 and 1. If a name (in the the form of *.png) is given, the figure will be saved with
    the specified name. If show is set to 'show', the plot will be shown.

    '''

    # conver the value name
    threshold = pval

    # extract the entropy values and find the entropy threshold
    results_df = entropy_calc(file, pval, obj=obj)
    entropy = results_df['entropy']
    # sort the entropy values in ascending order
    entropy = entropy.sort_values(ascending=True)
    entropy_threshold = np.percentile(entropy, q=threshold)

    # plot histogram
    fig = plt.gcf()
    plt.hist(entropy, bins='auto', log=True)
    plt.axvline(entropy_threshold, color='red')
    plt.xlabel('Entropy')
    plt.ylabel('Samples Per Bin')
    plt.title('Binned Feature Entropy')
    plt.legend(['P < {}'.format(threshold), 'Data'])
    fig.set_size_inches(10,10)


    if name == None and show != None:
        plot.show()
    elif name != None:
        fig.savefig(name, dpi=100)
    elif name != None and show != None:
        fig.savefig(name, dpi=100)
        plot.show()

    return('Done Plotting')



def main(argv=None):

    # read in command line variables
    args = docopt(__doc__, argv=argv)
    args['<counts_fn>'] = args.get('<counts_fn>')
    args['--percentile'] = args.get('--percentile')
    args['--output'] = args.get('--output')
    args['--plot-output'] = args.get('--plot-output')

    # use the .commons file processing
    data = CountMatrixFile(args['<counts_fn>'])

    # gather the variables
    file = data.counts
    pval = float(args['--percentile'])

    # if output or plot specified, convert to proper datatype
    # otherwise set to None
    if args['--output'] != None:
        output = str(args['--output'])
    else:
        output = None

    if args['--plot-output'] != None:
        plot = str(args['--plot-output'])
    else:
        plot = None

    # run the entropy_calc function
    results = entropy_calc(file, pval, obj='terminal')

    # if users specifies output name, write results to csv
    if output != None and plot == None:
        results.to_csv(output)
        return('Done')
    # if user specifies plot-output, write results to csv and
    # save figure to png
    elif output != None and plot != None:
        results.to_csv(output)
        plot_entropy(file, pval, name=plot, obj='terminal')
        return('Done')
    # if users desire only the plot, save figure to png
    elif output == None and plot != None:
        plot_entropy(file, pval, name=plot, obj='terminal')
        return('Done')
    # return results to stdout
    elif output == None and plot == None:
        f = sys.stdout
        results.to_csv(f, sep='\t')



if __name__ == '__main__':
    main()
