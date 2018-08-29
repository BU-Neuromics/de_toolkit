'''
Easy access to informative count matrix statistics. Each of these functions produces two outputs:

    a json formatted file containing relevant statistics in a machine-parsable format
    an optional human-friendly HTML page displaying the results

All of the commands accept a single counts file as input with optional arguments as indicated in the
documentation. By default, the JSON and HTML output files have the same basename without extension as
the counts file but including .json or .html as appropriate. E.g., counts.csv will produce counts.json
and counts.html in the current directory. These default filenames can be changed using optional command
line arguments --json=<json fn> and --html=<html fn> as appropriate for all commands. If <json fn>,
either default or specified, already exists, it is read in, parsed, and added to. The HTML report is
overwritten on every invocation using the contents of the JSON file.

Usage:
    detk-stats summary [options] <counts_fn>
    detk-stats base [options] <counts_fn>
    detk-stats coldist [options] <counts_fn>
    detk-stats rowdist [options] <counts_fn>
    detk-stats colzero [options] <counts_fn>
    detk-stats rowzero [options] <counts_fn>
    detk-stats entropy [options] <counts_fn>
    detk-stats pca [options] <counts_fn>

Options:
    -h --help       Access detailed help for individual commands
'''

cmd_opts = {
    'summary':'''\
Compute summary statistics on a counts matrix file.

This is equivalent to running each of these tools separately:

- base
- coldist
- rowdist
- colzero
- rowzero
- entropy
- pca

Usage:
    detk-stats summary [options] <counts_fn>

Options:
    -h --help
    --column-data=FN       Use column data provided in FN, only used in PCA
    --color-col=COLNAME    Use column data column COLNAME for coloring output plots
    --bins=BINS            Number of bins to use for the calculated
                           distributions [default: 20]
    --log                  log transform count statistics
    --density              Produce density distribution by dividing each distribution
                           by the appropriate sum
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file


''',
    'base':'''\
Calculate basic statistics of the counts file, including:
    number of samples
    number of rows

Usage:
    detk-stats base [options] <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file
''',
    'coldist':'''\
Column-wise distribution of counts

Compute the distribution of counts column-wise. Each column is subject to
binning by percentile, with output identical to that produced by np.histogram.

In the stats object, the fields are defined as follows:
    pct
        The percentiles of the distributions in the range 0 < pct < 100, by
        default in increments of 5. This defines the length of the dist and
        bins arrays in each of the objects for each sample.
    dists
        Array of objects containing one object for each column, described below.
    Each item of dists is an object with the following keys:
        name
            Column name from original file
        dist
            Array of raw or normalized counts in each bin according to the
            percentiles from pct
        bins
            Array of the bin boundary values for the distribution. Should
            be of length len(counts)+1. These are what would be the x-axis
            labels if this was plotted as a histogram.
        extrema
            Object with two keys, min and max, that contain the literal
            count values for counts that have a value larger or smaller than
            1.5*(inner quartile length) of the distribution. These could be
            marked as outliers in a boxplot, for example.

Usage:
    detk-stats coldist [options] <counts_fn>

Options:
    --bins=N               The number of bins to use when computing the counts
                           distribution [default: 20]
    --log                  Perform a log10 transform on the counts before
                           calculating the distribution. Zeros are omitted
                           prior to histogram calculation.
    --density              Return a density distribution instead of counts,
                           such that the sum of values in *dist* for each
                           column approximately sum to 1.
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file
''',
    'rowdist':'''\
Row-wise distribution of counts

Compute the distribution of counts row-wise. Each row is subject to binning by
percentile, with output identical to that produced by np.histogram.

In the stats object, the fields are defined as follows:
    pct
        The percentiles of the distributions in the range 0 < pct < 100, by
        default in increments of 5. This defines the length of the dist and
        bins arrays in each of the objects for each sample.
    dists
        Array of objects containing one object for each column, described
        below.
    Each item of dists is an object with the following keys:
        name
            Column name from original file
        dist
            Array of raw or normalized counts in each bin according to the
            percentiles from pct
        bins
            Array of the bin boundary values for the distribution. Should
            be of length len(counts)+1. These are what would be the x-axis
            labels if this was plotted as a histogram.
        extrema
            Object with two keys, min and max, that contain the literal
            count values for counts that have a value larger or smaller than
            1.5*(inner quartile length) of the distribution. These could be
            marked as outliers in a boxplot, for example.

Usage:
    detk-stats rowdist [options] <counts_fn>

Options:
    --bins=N               The number of bins to use when computing the counts
                           distribution [default: 20]
    --log                  Perform a log10 transform on the counts before calculating
                           the distribution. Zeros are omitted prior to histogram
                           calculation.
    --density              Return a density distribution instead of counts, such that
                           the sum of values in *dist* for each row approximately
                           sum to 1.
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file
''',
    'colzero':'''\
Column-wise distribution of zero counts

Compute the number and fraction of exact zero counts for each column.
The stats value is an array containing one object per column as follows:
    name
        column name
    zero_count
        absolute count of rows with exactly zero counts
    zero_frac
        zero_count divided by the number of rows
    col_mean
        the mean of counts in the column
    nonzero_col_mean
        the mean of only the non-zero counts in the column

Usage:
    detk-stats colzero [options] <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file
            ''',
    'rowzero':'''\
Row-wise distribution of zero counts

Compute the number and fraction of exact zero counts for each row.
The stats value is an array containing one object per row as follows:
    name
        row name
    zero_count
        absolute count of rows with exactly zero counts
    zero_frac
        zero_count divided by the number of rows
    row_mean
        the mean of counts in the row
    nonzero_row_mean
        the mean of only the non-zero counts in the row

Usage:
    detk-stats rowzero [options] <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file
''',
    'entropy':'''\
Row-wise sample entropy calculation

Sample entropy is a metric that can be used to identify outlier samples by locating
rows which are overly influenced by a single count value. This metric can be
calculated for a single row as follows:
    pi = ci/sumj(cj)
    sum(pi) = 1
    H = -sumi(pi*log2(pi))
Here, ci is the number of counts in sample i, pi is the fraction of reads contributed
by sample i to the overall counts of the row, and H is the Shannon entropy of the row
when using log2. The maximum value possible for H is 2 when using Shannon entropy.

Rows with a very low H indicate a row has most of its count mass contained in a small
number of columns. These are rows that are likely to drive outliers in downstream
analysis, e.g. differential expression.

The key entropies is an array containing one object per row with the following keys:
    name
        row name from counts file
    entropy
        the value of H calculated as above for that row

Usage:
    detk-stats [options] entropy <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file
''',
    'pca':'''\
Principal common analysis of the counts matrix.

This module performs PCA on a provided counts matrix and returns the principal
component weights, scores, and variances. In addition, the weights and scores
for each individual component can be combined to define the projection of each
sample along that component.

The PCA module can also accept a metadata file that contains information about
the samples in each column. The user can specify some of these columns to
include as variables for plotting purposes. The idea is that columns labeled
with the same class will be colored according to their class, such that
separations in the data can be more easily observed when projections are
plotted.

Usage:
    detk-stats pca [options] <counts_fn>

Options:
    -m FN --column-data=FN      Column data for annotating PCA results and
                                plots (experimental)
    -f NAME --column-name=NAME  Column name from provided column data for
                                annotation PCA results and plots (experimental)
    -o FILE --output=FILE       Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
    --json=<json_fn>            Name of JSON output file
    --html=<html_fn>            Name of HTML output file
'''
}
from collections import OrderedDict
import csv
from docopt import docopt
import json
import math
import matplotlib
matplotlib.use('agg')
import matplotlib.patches as ptches
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import pandas
import pkg_resources
import os.path
import seaborn as sns
from sklearn.decomposition import PCA
from string import Template
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale

from .common import *

class CountStatistics(OrderedDict) :
    '''
    Base class for holding count matrix statistics

    Each stats function in this module is a subclass of this class, which
    is itself a subclass of :py:class:`collections.OrderedDict`.
    '''
    @property
    def json(self) :
        '''
        Format the stats object into a form amenable to serializing with JSON

        Returns
        -------
        dict
            dictionary with keys 'name' and 'stats' containing the module name
            and dictionary of stats in the object
        '''
        return { 'name': self.name,
                'stats': dict(self) }
    @property
    def tabular(self) :
        '''
        Construct tabular output of the stats object

        Returns
        -------
        list
            list of lists containing tabular stats data, first row contains
            column names
        '''
        return None
    @property
    def html(self) :
        '''
        Construct html output of the stats object

        Returns
        -------
        string
            string containing html and javascript representation of this stat
            module
        '''
        return None
    @property
    def name(self) :
        'Name of this stats object, by default the class name in all lower case'
        return self.__class__.__name__.lower()

def summary(count_mat,
        bins=20,
        log=False,
        density=False) :
    '''
    Compute summary statistics on a counts matrix file.

    This is equivalent to running each of these tools separately:

    - base
    - coldist
    - rowdist
    - colzero
    - rowzero
    - entropy
    - pca

    Parameters
    ----------
    count_mat : CountMatrix object
        count matrix object
    bins : int
        number of bins, passed to coldist and rowdist
    log : bool
        perform log10 transform of counts in coldist and rowdist
    density : bool
        return a density distribution from coldist and rowdist

    Returns
    -------
    list
        list of CountStatistics subclasses for each of the called submodules
    '''

    total_output = [
        Base(count_mat),
        ColDist(count_mat, bins, log, density),
        RowDist(count_mat, bins, log, density),
        ColZero(count_mat),
        RowZero(count_mat),
        Entropy(count_mat),
        CountPCA(count_mat)
    ]

    return total_output

class Base(CountStatistics) :
    '''
        Basic statistics of the counts file

        The most basic statistics of the counts file, including:
        - number of columns
        - number of rows

    '''
    def __init__(self, count_mat) :

        #Get counts, number of columns, and number of rows
        self.num_rows, self.num_cols = count_mat.counts.shape

        #Format output
        self['num_cols'] = self.num_cols
        self['num_rows'] = self.num_rows

    @property
    def tabular(self):
        '''
        Example tabular output::

            +base------+-----+
            | stat     | val |
            +----------+-----+
            | num_cols | 4   |
            | num_rows | 3   |
            +----------+-----+
        '''
        return [
                ['stat','val'],
                ['num_cols',self['num_cols']],
                ['num_rows',self['num_rows']]
               ]

    @property
    def json(self):
        '''
        Example JSON output::

            {
              'name': 'base',
              'stats': {
                'num_cols': 50,
                'num_rows': 27143
              }
            }
        '''
        return {'name': self.name, 'stats': dict(self)}

class ColDist(CountStatistics) :
    '''
        Column-wise distribution of counts

        Compute the distribution of counts column-wise. Each column is subject
        to binning by percentile, with output identical to that produced by
        np.histogram.

        Parameters
        ----------
        count_mat : CountMatrix
            count matrix containing counts
        bins : int
            number of bins to use when computing distribution
        log : bool
            take the log10 of counts prior to computing distribution
        density : bool
            return densities rather than absolute bin counts for the
            distribution, densities sum to 1

    '''
    def __init__(self,count_mat,bins=100,log=False,density=False):
        self['pct'] = list(100*(_+1)/bins for _ in range(bins))

        self['dists'] = []

        for s in count_mat.sample_names:
            #to access the data in each column
            data = getattr(count_mat.counts,s).tolist()

            #Take the log10 of each count if log option is specified
            if log :
                data=list(filter(lambda a: a != 0.0, data))
                data=np.log10(data)

            #for the upper and lower outliers
            Q1 = np.percentile(data, 25)
            Q3 = np.percentile(data, 75)
            IQR =  np.percentile(data, 75) - np.percentile(data, 25)

            #for the histogram bin edges and count numbers
            if density :
                (n, dist_bins, patches) = plt.hist(
                        data,
                        bins=bins,
                        label='hst',
                        weights=np.zeros_like(np.asarray(data)) + 1. / np.asarray(data).size
                )
            else:
                (n, dist_bins, patches) = plt.hist(data, bins=bins, label='hst')

            #make the dict for each sample
            self['dists'].append(
                    {
                        'name':s,
                        'dist':list(n),
                        'bins':list(dist_bins)[1:],
                        'extrema': {
                            'lower':[i for i in data if i < Q1-1.5*IQR],
                            'upper':[i for i in data if i > Q3+1.5*IQR]
                        }
                    }
                )

    @property
    def tabular(self) :
        '''
        Tabular output is a table where each row corresponds to a column
        with column name as the first column. The next columns are broken
        into two parts:

          - the bin start values, named like bin_N, where N is the percentile
          - the bin count values, named like dist_N, where N is the percentile
        '''
        colnames = ['colname']+\
                ['bin_{:.1f}'.format(_) for _ in self['pct']]+\
                ['dist_{:.1f}'.format(_) for _ in self['pct']]
        res = [colnames]
        for dist in self['dists'] :
            res.append([dist['name']]+dist['bins']+dist['dist'])
        return res
    @property
    def json(self) :
        '''
        In the JSON object, the fields are defined as follows

        pct
            The percentiles of the distributions in the range 0 < pct <
            100, by default in increments of 5. This defines the length of
            the dist and bins arrays in each of the objects for each sample.
        dists
            Array of objects containing one object for each column,
            described below.

        Each item of dists is an object with the following keys:

        name
            Column name from original file
        dist
            Array of raw or normalized counts in each bin according to
            the percentiles from pct
        bins
            Array of the bin boundary values for the distribution.
            Should be of length len(counts)+1. These are what would be
            the x-axis labels if this was plotted as a histogram.
        extrema
            Object with two keys, lower and upper, that contain the
            literal count values for counts that have a value larger or
            smaller than 1.5*(inner quartile length) of the
            distribution. These could be marked as outliers in a
            boxplot, for example.

        Example JSON output::

            {
              'name': 'coldist',
              'stats': {
                'pct' : [ 5, 10, 20, ..., 95 ],
                'dists' : [
                  {
                    'name': 'H_0001',
                    'dist': [ 129, 317, 900, 1325, ...],
                    'bins': [ 100, 200, 300, 400, ...],
                    'extrema': {
                      'lower': [1, 2, 5],
                      'upper': [19325, 5233]
                      }
                    ]
                  },
                  {
                    'name': 'H_0002',
                    'dist': [ 502, 127, 222, 591, ...],
                    'bins': [ 6000, 6200, 6400, 6600, ...],
                    'extrema': {
                      'lower': [419, 2, 20],
                      'upper': [21999,74381]
                      }
                    ]
                  }
                ]
              }
            }
        '''
        return {'name': self.name, 'stats': dict(self)}

class RowDist(CountStatistics):
    '''
        Row-wise distribution of counts

        Identical to coldist except calculated across rows. The name key is
        rowdist, and the name key of the items in dists is the row name from
        the counts file.

        Parameters
        ----------
        count_mat : CountMatrix
            count matrix containing counts
        bins : int
            number of bins to use when computing distribution
        log : bool
            take the log10 of counts prior to computing distribution
        density : bool
            return densities rather than absolute bin counts for the
            distribution, densities sum to 1
    '''
    def __init__(self, count_obj, bins=100, log=False, density=False) :

        self['pct'] = list(100*(_+1)/bins for _ in range(bins))
        self['dists'] = []

        for i in range(len(count_obj.feature_names)):
            #to access the data in each row
            data = count_obj.counts.iloc[i].tolist()

            #Compute log10 of each count if log option is specified
            if log :
                data=list(filter(lambda a: a != 0.0, data))
                data=np.log10(data)
            
            #for the upper and lower outliers
            Q1 = np.percentile(data, 25)
            Q3 = np.percentile(data, 75)
            IQR =  np.percentile(data, 75) - np.percentile(data, 25)

            #for the histogram bin edges and count numbers
            if density == 1:
                (n, dist_bins, patches) = plt.hist(
                        data,
                        bins=bins,
                        label='hist',
                        weights=np.zeros_like(np.asarray(data)) + 1. / np.asarray(data).size
                    )
            else:
                (n, dist_bins, patches) = plt.hist(data, bins=bins, label='hst')

            #make the dict for each row
            self['dists'].append(
                    {
                        'name':count_obj.feature_names[i],
                        'dist':list(n),
                        'bins':list(dist_bins)[1:],
                        'extrema': {
                            'lower':[i for i in data if i < Q1-1.5*IQR],
                            'upper':[i for i in data if i > Q3+1.5*IQR]
                        }
                    }
                )
    @property
    def tabular(self) :
        '''
            Tabular output is a table where each row corresponds to a row
            with row name as the first column. The next columns are broken
            into two parts:

              - the bin start values, named like bin_N, where N is the
                percentile
              - the bin count values, named like dist_N, where N is the
                percentile
        '''
        colnames = ['rowname']+\
              ['bin_{}'.format(_) for _ in self['pct']]+\
              ['dist_{}'.format(_) for _ in self['pct']]
        res = [colnames]
        for dist in self['dists'] :
            res.append([dist['name']]+dist['bins']+dist['dist'])
        return res

class ColZero(CountStatistics) :
    '''
        Column-wise distribution of zero counts
    
        Compute the number and fraction of exact zero counts for each column.

    '''
    def __init__(self,count_mat) :
        #Get counts, number of columns, number of rows, and sample names
        num_rows, num_cols = count_mat.counts.shape
        col_names=count_mat.sample_names

        #Calculate zero counts, zero fractions, means, and nonzero means for each column
        zero_counts = []
        zero_fracs = []
        col_means = []
        nonzero_col_means = []
        for s in col_names:
            data = getattr(count_mat.counts,s).tolist()
            zero_counts.append(data.count(0.0))
            zero_fracs.append(data.count(0.0)/len(data))
            col_means.append(sum(data)/len(data))
            if len(data) != data.count(0.0):
                nonzero_col_means.append(sum(data)/((len(data)-data.count(0.0))))
            else:
                nonzero_col_means.append(0.0)
        
        self['zeros'] = []

        for i in range(0, num_cols):
            col = {}
            col['name'] = col_names[i]
            col['zero_count'] = zero_counts[i]
            col['zero_frac'] = zero_fracs[i]
            col['mean'] = col_means[i]
            col['nonzero_mean'] = nonzero_col_means[i]
            self['zeros'].append(col)

    @property
    def tabular(self) :
        '''
            Tabular output is a table where each row corresponds to a column
            with the following fields:

            - name: Column name
            - zero_count: Number of zero counts
            - zero_frac: Fraction of zero counts
            - mean: Overall mean count
            - nonzero_mean: Mean of non-zero counts only
        '''
        res = [['name','zero_count','zero_frac','mean','nonzero_mean']]
        for col in self['zeros'] :
            res.append([col[_] for _ in res[0]])
        return res
    @property
    def json(self):
        '''
        The stats value is an array containing one object per column as follows:

        name
            column name
        zero_count
            absolute count of rows with exactly zero counts
        zero_frac
            zero_count divided by the number of rows
        col_mean
            the mean of counts in the column
        nonzero_col_mean
            the mean of only the non-zero counts in the column

        Example JSON output::

            {
              'name': 'colzero',
              'stats': {
                'zeros' : [
                  {
                    'name': 'col1',
                    'zero_count': 20,
                    'zero_frac': 0.2,
                    'mean': 101.31,
                    'nonzero_mean': 155.23
                  },
                  {
                    'name': 'col2',
                    'zero_count': 0,
                    'zero_frac': 0,
                    'mean': 3021.92,
                    'nonzero_mean': 3021.92
                  },
                ]
              }
            }
        '''
        return {'name': self.name, 'stats': dict(self)}

class RowZero(CountStatistics):
    '''
        Row-wise distribution of zero counts
    
        Identical to colzero, only computed across rows instead of columns. The name 
        key is rowzero, and the name key of the items in dists is the row name from 
        the counts file.
    '''
    def __init__(self,count_mat):

        #Get counts, number of columns, number of rows, and gene names
        cnts = count_mat.counts.values
        num_cols=len(cnts[0])
        num_rows=len(cnts)
        row_names = count_mat.feature_names

        #Calculate zero counts, zero fractions, means, and nonzero means for each row
        zero_counts = []
        zero_fracs = []
        row_means = []
        nonzero_row_means = []
        for i in range(len(row_names)):
            data = count_mat.counts.iloc[i].tolist()
            zero_counts.append(data.count(0.0))
            zero_fracs.append(data.count(0.0)/len(data))
            row_means.append(sum(data)/len(data))
            if len(data) != data.count(0.0):
                nonzero_row_means.append(sum(data)/(len(data)-data.count(0.0)))
            else:
                nonzero_row_means.append(0.0)

        self['zeros'] = []

        for i in range(0, num_rows):
            row = {}
            row['name'] = row_names[i]
            row['zero_count'] = zero_counts[i]
            row['zero_frac'] = zero_fracs[i]
            row['mean'] = row_means[i]
            row['nonzero_mean'] = nonzero_row_means[i]
            self['zeros'].append(row)

    @property
    def tabular(self) :
        '''
            Tabular output is a table where each row corresponds to a row
            with the following fields:

              - name: Row name
              - zero_count: Number of zero counts
              - zero_frac: Fraction of zero counts
              - mean: Overall mean count
              - nonzero_mean: Mean of non-zero counts only
        '''
        res = [['name','zero_count','zero_frac','mean','nonzero_mean']]
        for col in self['zeros'] :
            res.append([col[_] for _ in res[0]])
        return res

class Entropy(CountStatistics) :
    '''
    Row-wise sample entropy calculation

    Sample entropy is a metric that can be used to identify outlier samples
    by locating rows which are overly influenced by a small number of count
    values. This metric can be calculated for a single row as follows::

        pi = ci/sumj(cj)
        sum(pi) = 1
        H = -sumi(pi*log2(pi))

    Here, ci is the number of counts in sample i, pi is the fraction of
    reads contributed by sample i to the overall counts of the row, and H
    is the `Shannon entropy`_ of the row when using log2. The maximum value
    possible for H is 2 when using Shannon entropy.

    Rows with a very low H indicate a row has most of its count mass
    contained in a small number of columns. These are rows that are likely
    to drive outliers in downstream analysis, e.g. differential expression.

    .. _Shannon entropy: https://en.wikipedia.org/wiki/Entropy_(information_theory)
    '''
    def __init__(self,count_mat) :

        #Get counts, number of columns, number of rows, and gene names
        cnts = count_mat.counts.values
        num_cols=len(cnts[0])
        num_rows=len(cnts)
        row_names = count_mat.feature_names

        probs = []
        for i in range(len(row_names)):
            data = count_mat.counts.iloc[i].tolist()
            row_prob = []
            for item in data:
                if sum(data) != 0:
                    row_prob.append(item/sum(data))
                else:
                    row_prob.append(0.0)
            probs.append(row_prob)

        #Calculate entropies
        entropies = []
        for i in range(0, num_rows):
            H = 0.0
            row_probs = probs[i]
            for j in range(0, len(row_probs)):
                if row_probs[j] != 0.0:
                    H += row_probs[j]*math.log(row_probs[j], 2)
            H = -1*H
            entropies.append(H)

        #Format output
        self['entropies'] = []

        for i in range(0, num_rows):
            row = {}
            row['name'] = row_names[i]
            row['entropy'] = entropies[i]
            self['entropies'].append(row)

    @property
    def tabular(self) :
        '''
        Tabular output is a table where each row corresponds to a row
        with the following fields:

          - name: Row name
          - entropy: sample entropy for the row
        '''
        res = [['name','entropy']]
        for col in self['entropies'] :
            res.append([col[_] for _ in res[0]])
        return res
    @property
    def json(self) :
        '''
        The key entropies is an array containing one object per row with the
        following keys:

        name
            row name from counts file
        entropy
            the value of H calculated as above for that row

        Example JSON output::

            [
              'name': 'entropy',
              'stats': {
                'entropies': [
                  {
                    'name': 'gene1',
                    'entropy': 1.013
                  },
                  {
                    'name': 'gene2',
                    'entropy': 0.001
                  }
                ]
              }
            ]
        '''
        return {'name': self.name, 'stats': dict(self)}

class CountPCA(CountStatistics) :
    '''
    Principal common analysis of the counts matrix.

    This module performs PCA on a provided counts matrix and returns the
    principal component weights, scores, and variances. In addition, the
    weights and scores for each individual component can be combined to define
    the projection of each sample along that component.  

    The PCA module can also use a counts matrix that has associated column data
    information about the samples in each column. The user can specify some of
    these columns to include as variables for plotting purposes. The idea is
    that columns labeled with the same class will be colored according to their
    class, such that separations in the data can be more easily observed when
    projections are plotted.
    '''
    def __init__(self,count_mat) :

        # get counts from file and scale counts
        # counts matrices are n_features x n_samples, need to transpose
        # since PCA expects n_samples x n_features
        cnts = scale(count_mat.counts.values.astype(float).T)

        # sanity check, column mean==0
        assert np.allclose(cnts.mean(axis=0),0)
        assert cnts.shape[0] == count_mat.counts.shape[1]

        # perform PCA and fit to the data
        pca = PCA(n_components=min(*cnts.shape))
        pca.fit(cnts)
        X = pca.transform(cnts)

        # get sample names
        sample_names = list(count_mat.counts.columns)

        # format output
        self['column_names'] = sample_names
        self['column_variables'] = {}

        # if metadata option is given, get column variables
        if count_mat.column_data is not None :
            self['column_variables'] = {k:list(v) for k,v in count_mat.column_data.iterrows()}

        self['components'] = []
        for i in range(0, pca.n_components_):
            comp = {}
            comp['name'] = 'PC' + str(i+1)
            comp['scores'] = [row[i] for row in X]
            comp['projections'] = [row[i] for row in pca.components_]
            comp['perc_variance'] =  pca.explained_variance_ratio_[i]
            if np.isnan(comp['perc_variance']) :
                raise Exception('nan encountered in calculating PCA component '
                        'percent variance, this means the counts features have '
                        'zero total variance, cannot compute PCA. Examine your '
                        'counts matrix if you did not expect this?')
            self['components'].append(comp)
    @property
    def name(self):
        return 'pca'
    @property
    def tabular(self) :
        '''
        Tabular output is a table where each row corresponds to a column
        in the counts matrix with the following fields:

        name
            name of the column for the row
        PC*X*_*YY*
            projections of principal component X (e.g. 1) that explains YY
            percent of the variance for each column 
        '''
        res = [['colname']+self['column_names']]
        for comp in self['components'] :
            name = '{}_{:03d}'.format(comp['name'],int(100*comp['perc_variance']))
            res.append([name]+comp['projections'])
        # transpose the list of lists
        res = list(zip(*res))
        return res
    @property
    def json(self) :
        '''
        Example JSON output::

            [
                'name': 'pca',
                'stats': {
                    'column_names': ['sample1','sample2',...],
                    'column_variables': {
                        'sample_type':['HD','HD','C',...],
                        'sample_batch':['Batch1','Batch2','Batch2',...]
                    },
                    'components': [
                        {
                            'name': 'PC1',
                            'scores': [0.126,0.975,...], # length n
                            'projections': [-8.01,5.93,...], # length m, ordered by 'column_names'
                            'perc_variance': 0.75
                        },
                        {
                            'name': 'PC2',
                            'scores' : [0.126,0.975,...], # length n
                            'projections': [5.93,-5.11,...], # length m
                            'perc_variance': 0.22
                        }
                    ]
                }
            ]
        '''
        return {'name': self.name, 'stats': dict(self)}

def format_json(filename, output):

    # new dict for holding stats recs
    output_dict = OrderedDict()

    # see if filename already exists
    if os.path.isfile(filename) :
        # read in the existing file
        with open(filename) as f :
            previous_output = json.load(f)
            # examine the file for correctness, each array object must have a
            # 'name' key
            for d in previous_output :
                if 'name' not in d :
                    raise Exception('Malformed detk-stats JSON record in '
                            'pre-existing file, no name key:',str(d))
                output_dict[d['name']] = d

    # go through the given output and update output_dict appropriately
    for d in output :
        if not hasattr(d,'json') :
          raise Exception('Could not serialize output, could not find .json '
              'attribute on output object:',str(d))
        output_dict[d.name] = d.json

    # write out values in output_dict
    with open(filename,'w') as f :
        json.dump(list(output_dict.values()),f)

# monkeypatch mpld3._display.NumpyEncoder pending fix to
# https://github.com/mpld3/mpld3/issues/434
import mpld3
class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16,np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, 
            np.float64)):
            return float(obj)
        elif isinstance(obj,(np.ndarray,)): #### This is the fix
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
mpld3._display.NumpyEncoder = NumpyEncoder

def format_html(html_fn, json_fn, counts_obj, color_col):

    #HTML template that will be filled in using the available JSON data
    resource = pkg_resources.resource_string(__name__, 'html_template.html')
    resource = resource.decode('utf-8')
    s = Template(resource)

    output_dict = OrderedDict()
    with open(json_fn) as f:
        for d in json.load(f) :
            output_dict[d['name']] = d

    #Format base HTML output (table)
    if 'base' in output_dict:
        base_hide=''
        base_output = output_dict['base']
        num_cols = base_output['stats']['num_cols']
        num_rows = base_output['stats']['num_rows']
    else:
        base_hide='hidden'
        num_cols=''
        num_rows=''

    #Format colzero HTML output (bar chart of samples and zero fractions)
    if 'colzero' in output_dict:
        colzero_hide=''
        colzero_output = output_dict['colzero']
        zeros_list = colzero_output['stats']['zeros']
        zero_fracs = []
        column_names = []
        bar_names = []
        for item in zeros_list:
            zero_fracs.append(item['zero_frac'])
            column_names.append(item['name'])
            bar_names.append('Zero Fraction = {0:.3f}'.format(item['zero_frac']))

        x = [i for i in range(1, len(zeros_list)+1)]
        
        fig = plt.figure()
        fig.clf()
        mpld3.plugins.clear(fig)
        bars=plt.bar(x, zero_fracs, tick_label=column_names, color='red')
        plt.title('Zero Fractions Bar Chart', fontsize=20)
        plt.xlabel('Sample', fontsize=15)
        plt.ylabel('Zero Fraction', fontsize=15)

        for i, bar in enumerate(bars.get_children()):
            tooltip = mpld3.plugins.LineLabelTooltip(bar, bar_names[i], hoffset=10)
            mpld3.plugins.connect(fig, tooltip)

        colzero = mpld3.fig_to_html(fig)

    else:
        colzero_hide='hidden'
        colzero=''

    #Format rowzero HTML output (scatterplot of zero fraction vs. nonzero mean and histogram of zero fracs)
    if 'rowzero' in output_dict:
        rowzero_hide=''
        rowzero_output = output_dict['rowzero']
        zeros_list = rowzero_output['stats']['zeros']
        zero_fracs = []
        nonzero_means = []
        means = []
        row_names = []
        row_names2 = []
        for item in zeros_list:
            zero_fracs.append(item['zero_frac'])
            nonzero_means.append(item['nonzero_mean'])
            row_names.append('{0}: {1:.2f}, {2:.2f}'.format(item['name'], item['zero_frac'], item['nonzero_mean']))
            means.append(item['mean'])
            row_names2.append('{0}: {1:.2f}, {2:.2f}'.format(item['name'], item['zero_frac'], item['mean']))
        
        fig1 = plt.figure(1)
        fig1.clf()
        mpld3.plugins.clear(fig1)
        points = plt.scatter(zero_fracs, nonzero_means)
        plt.title('Zero Fractions vs. Nonzero Means', fontsize=20)
        plt.xlabel('Zero Fraction', fontsize=15)
        plt.ylabel('Nonzero Mean', fontsize=15)
        tooltip1 = mpld3.plugins.PointHTMLTooltip(points, row_names, hoffset=10)
        mpld3.plugins.connect(fig1, tooltip1)

        #print(type(zero_fracs), type(nonzero_means), type(row_names))

        fig2 = plt.figure(2)
        fig2.clf()
        mpld3.plugins.clear(fig2)
        mean_points = plt.scatter(zero_fracs, means)
        plt.title('Zero Fractions vs. Means', fontsize=20)
        plt.xlabel('Zero Fraction', fontsize=15)
        plt.ylabel('Mean', fontsize=15)
        tooltip2 = mpld3.plugins.PointHTMLTooltip(mean_points, row_names2, hoffset=10)
        mpld3.plugins.connect(fig2, tooltip2)

        fig3 = plt.figure(3)
        fig3.clf()
        mpld3.plugins.clear(fig3)
        n, bins, patches = plt.hist(zero_fracs, bins=10, range=(0.0, 1.0), color='green')
        plt.title('Zero Fractions Histogram', fontsize=20)
        plt.xlabel('Zero Fraction', fontsize=15)
        plt.ylabel('Frequency', fontsize=15)
        ticks = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        plt.xticks(ticks)
        bar_names = ['{}'.format(i) for i in n]

        for i, patch in enumerate(patches):
            tooltip3 = mpld3.plugins.LineLabelTooltip(patch, bar_names[i], hoffset=10)
            mpld3.plugins.connect(fig3, tooltip3)
        
        rowzero_scatter = mpld3.fig_to_html(fig1)
        rowzero_scatter2 = mpld3.fig_to_html(fig2)
        rowzero_hist = mpld3.fig_to_html(fig3)

    else:
        rowzero_hide='hidden'
        rowzero_scatter=''
        rowzero_scatter2=''
        rowzero_hist=''

    #Format entropy HTML output (histogram)
    if 'entropy' in output_dict:
        entropy_hide=''
        entropy_output = output_dict['entropy']
        entropies = entropy_output['stats']['entropies']
        entropy_list = []
        for item in entropies:
            entropy_list.append(item['entropy'])
        fig = plt.figure()
        fig.clf()
        mpld3.plugins.clear(fig)
        n, bins, patches = plt.hist(entropy_list, color='purple')
        plt.title('Entropy Histogram', fontsize=20)
        plt.xlabel('Entropy', fontsize=15)
        plt.ylabel('Frequency', fontsize=15)
        
        bar_names = ['{}'.format(i) for i in n]
        for i, patch in enumerate(patches):
            tooltip = mpld3.plugins.LineLabelTooltip(patch, bar_names[i], hoffset=10)
            mpld3.plugins.connect(fig, tooltip)

        entropy = mpld3.fig_to_html(fig)
    else:
        entropy_hide='hidden'
        entropy=''

    #Format coldist HTML output (box plots for each column)
    if 'coldist' in output_dict:
        coldist_hide=''
        cnts = counts_obj.counts.values
        names = counts_obj.sample_names
        row_names = counts_obj.feature_names
        fig = plt.figure()
        fig.clf()
        mpld3.plugins.clear(fig)
        box = plt.boxplot(cnts, labels=names)
        
        outliers = []
        for item in box['fliers']:
            outliers.append(list(item.get_data()[1]))

        i=0
        for points, name in zip(outliers, names):
            gene_name = []
            for point in points:
                ind = list(cnts[:,i]).index(point)
                gene_name.append(row_names[ind])
            tooltip = mpld3.plugins.PointHTMLTooltip(box['fliers'][i], gene_name, hoffset=10)
            mpld3.plugins.connect(fig, tooltip)
            i+=1
        
        for item in box['medians']:
            median = ['Median = {}'.format(item.get_data()[1][0])]
            tooltip = mpld3.plugins.LineLabelTooltip(item, median, hoffset=10)
            mpld3.plugins.connect(fig, tooltip)

        for item in box['boxes']:
            Q = ['Q1 = {}, Q3 = {}'.format(item.get_data()[1][0], item.get_data()[1][2])]
            tooltip = mpld3.plugins.LineLabelTooltip(item, Q, hoffset=10)
            mpld3.plugins.connect(fig, tooltip)
        
        for item in box['caps']:
            cap = ['Cap = {}'.format(item.get_data()[1][0])]
            tooltip = mpld3.plugins.LineLabelTooltip(item, cap, hoffset=10)
            mpld3.plugins.connect(fig, tooltip)        

        plt.title('Coldist Boxplot', fontsize=20)
        plt.ylabel('Count', fontsize=15)
        plt.xlabel('Sample Name', fontsize=15)
        coldist_boxplot = mpld3.fig_to_html(fig)
        plt.clf()
    else:
        coldist_hide = 'hidden'
        coldist_boxplot = ''

    #Format PCA HTML output (Scree plot and swarm plots for projections)
    if 'pca' in output_dict:
        pca_hide = ''
        pca_output = output_dict['pca'].get('stats')
        perc_variance = []
        names = []
        projections = []
        components = pca_output.get('components')
        for item in components:
            perc_variance.append(item.get('perc_variance'))
            names.append(item.get('name'))        
            projections.append(item.get('projections'))

        cumulative_variance = []
        cumulative_variance.append(perc_variance[0])
        for i in range(1, len(perc_variance)):
            cumulative_variance.append(cumulative_variance[i-1]+perc_variance[i])

        x = [i for i in range(0, len(perc_variance))]
        fig = plt.figure(1)
        fig.clf()
        mpld3.plugins.clear(fig)
        plt.plot(x, perc_variance, label='Variance')
        var, = plt.plot(x, perc_variance, label='Variance')
        cumulative, = plt.plot(x, cumulative_variance, label='Cumulative Variance')
        plt.xticks(x, names, rotation='vertical')
        plt.title('PCA Scree Plot')
        plt.ylabel('Proportion of Variance')
        plt.xlabel('Principle Components')
        plt.legend(handles=[var,cumulative])
        pca_scree=mpld3.fig_to_html(fig)    

        column_variables = pca_output['column_variables']
        if color_col is None :
            if len(column_variables)!=0: 
                color_col = list(column_variables)[0]
            else :
                color_col = 'data'
       
        sample_type = column_variables.get(color_col)
        if sample_type is None:
            sample_type = ['data' for i in range(len(projections))]

        fig2 = plt.figure(2)    
        fig2.clf()
        mpld3.plugins.clear(fig2)
        d = []
        for name, projection, variance in zip(names, projections, perc_variance):
            if variance >= 0.05:
                for i in range(0, len(projection)):
                    xlabel = name + ': ' + '{0:.3f}'.format(variance*100.0) + '%'
                    d.append([xlabel, projection[i], sample_type[i]])

        df = pandas.DataFrame(d, columns=['Principle Components', 'Projection', color_col])
        sns.set_style('whitegrid')
        palette_colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'black']
        ax = sns.swarmplot(
                x='Principle Components',
                y='Projection',
                data=df,
                hue=color_col,
                palette=sns.color_palette(palette_colors)
        )
        labels = []
        for item in sample_type:
            if item not in labels:
                labels.append(item)
        colors = sns.color_palette(palette_colors).as_hex()[:len(labels)]
        handles = [ptches.Patch(color=col, label=lab) for col, lab in zip(colors, labels)]
        plt.legend(handles=handles, title=color_col)
        plt.title('PCA Swarmplot')
        pca_swarm=mpld3.fig_to_html(fig2)

    else:
        pca_hide = 'hidden'
        pca_scree = ''
        pca_swarm = ''

    #Write all outputs to HTML file
    html_output = s.substitute(base_hide=base_hide, num_cols=num_cols, num_rows=num_rows,
                               colzero_hide=colzero_hide, colzero=colzero,
                               rowzero_hide=rowzero_hide, rowzero_scatter=rowzero_scatter, 
                               rowzero_hist=rowzero_hist, rowzero_scatter2=rowzero_scatter2,
                               entropy_hide=entropy_hide, entropy=entropy,
                               coldist_hide=coldist_hide, coldist_boxplot=coldist_boxplot,
                               pca_hide=pca_hide, pca_scree=pca_scree, pca_swarm=pca_swarm)
    html_fn = open(html_fn, 'w')
    html_fn.write(html_output)
    html_fn.close()

    # close matplotlib figures to free memory
    plt.close('all')

def main(argv=sys.argv) :

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts) :
        docopt(__doc__)
    argv = argv[1:]
    cmd = argv[0]

    # all modes have a counts file argument

    if cmd == 'pca' :
        args = docopt(cmd_opts['pca'],argv)
        counts_obj = CountMatrixFile(
                args['<counts_fn>'],
                column_data_f=args['--column-data']
            )
        output = CountPCA(counts_obj)
    elif cmd == 'summary' :
        args = docopt(cmd_opts['summary'],argv)
        counts_obj = CountMatrixFile(
                args['<counts_fn>'],
                column_data_f=args['--column-data']
            )
        output = summary(counts_obj
          ,int(args['--bins'])
          ,args['--log']
          ,args['--density']
        )
    elif cmd == 'coldist' :
        args = docopt(cmd_opts['coldist'],argv)
        counts_obj = CountMatrixFile(args['<counts_fn>'])
        output = ColDist(counts_obj
          ,bins=int(args['--bins'])
          ,log=args['--log']
          ,density=args['--density']
        )
    elif cmd == 'rowdist' :
        args = docopt(cmd_opts['rowdist'],argv)
        counts_obj = CountMatrixFile(args['<counts_fn>'])
        output = RowDist(counts_obj
          ,bins=int(args['--bins'])
          ,log=args['--log']
          ,density=args['--density']
        )
    elif cmd == 'colzero' :
        args = docopt(cmd_opts['colzero'],argv)
        counts_obj = CountMatrixFile(args['<counts_fn>'])
        output = ColZero(counts_obj)
    elif cmd == 'rowzero' :
        args = docopt(cmd_opts['rowzero'],argv)
        counts_obj = CountMatrixFile(args['<counts_fn>'])
        output = RowZero(counts_obj)
    elif cmd == 'entropy' :
        args = docopt(cmd_opts['entropy'],argv)
        counts_obj = CountMatrixFile(args['<counts_fn>'])
        output = Entropy(counts_obj)
    elif cmd == 'base' :
        args = docopt(cmd_opts['base'],argv)
        counts_obj = CountMatrixFile(args['<counts_fn>'])
        output = Base(counts_obj)

    # make output a list if it is a singleton
    if not isinstance(output,list) :
        output = [output]

    #Obtain string used to name output files, unless filename is specified
    filename_prefix = os.path.splitext(args['<counts_fn>'])[0]

    outf = sys.stdout
    if args['--output'] != 'stdout' :
        outf = open(args['--output'],'wt')

    if args['--format'] == 'table' :
        from terminaltables import AsciiTable
        for out in output :
            table = AsciiTable(out.tabular)
            table.title = out.name
            outf.write(table.table+'\n')

    else : # csv is default
        out_writer = csv.writer(outf,delimiter=',')

        # write out the tabular data
        if len(output) == 1 :
            out_writer.writerows(output[0].tabular)
        else :
            for out in output :
                out_writer.writerow(['#{}'.format(out.name)])
                out_writer.writerows(out.tabular)

    #Check if JSON file option was specified
    json_fn = args.get('--json')
    if json_fn is None:
        json_fn = filename_prefix+'.json'

    format_json(json_fn, output)

    # determine the html filename
    html_fn = args.get('--html')
    if html_fn is None:
        html_fn = filename_prefix+'.html'

    # if user specified no html fn, or html_fn != 'None', then we are
    # writing out an html file
    if html_fn != 'None' :
        format_html(html_fn, json_fn, counts_obj, args.get('--color-col'))

if __name__ == '__main__':
    main()
