``stats`` - Count Matrix Statistics
===================================

Easy access to informative count matrix statistics. Each of these functions
produces two outputs:

- a json_ formatted file containing relevant statistics in a machine-parsable
  format
- a human-friendly HTML page displaying the results

All of the commands accept a single counts file as input with optional
arguments as indicated in the documentation. By default, the JSON and HTML
output files have the same basename without extension as the counts file but
including *.json* or *.html* as appropriate. E.g., *counts.csv* will produce
*counts.json* and *counts.html* in the current directory. These default
filenames can be changed using optional command line arguments ``--json=<json
fn>`` and ``--html=<html fn>`` as appropriate for all commands. If ``<json
fn>``, either default or specified, already exists, it is read in, parsed, and
added to.  The HTML report is overwritten on every invocation using the
contents of the JSON file.

.. _json: http://www.json.org/

JSON output format
------------------

The JSON file produced by these modules is formatted as a JSON array containing
objects that each correspond to a stats module. For example::

  [
    {
      'name': 'base',
      'stats': {
        'num_cols': 50,
        'num_rows': 27143
      }
    },
    {
      'name': 'coldist',
      'stats': {
        'pct' : [ 0, 5, 10, 20, ...],
        'counts' : [
          {
            'name': 'H_0001',
            'counts': [ 129, 317, 900, 1325, ...]
            'frac': [ 0.01, 0.02, 0.04, 0.06, ...]
          },
          {
            'name': 'H_0002',
            'counts': [ 502, 127, 222, 591, ...]
            'frac': [ 0.05, 0.01, 0.02, 0.05, ...]
          }
        ]
      }
    },
    {
      'name': 'rowdist',
      'stats': ...
    }
    ...
  ]

The object format for each module is described in detail below.

``summary`` - Summary Statistics
--------------------------------

Compute summary statistics on a counts matrix file::

  detk-stats [--json=<json_fn>] [--html=<html_fn>] summary <counts file>

This command is equivalent to running each of the following stats commands:

- base_
- coldist_
- rowdist_
- colzero_
- rowzero_
- entropy_

concatenating the results.

.. _base:

``base`` - Basic statistics
---------------------------

Usage::

  detk-stats base <counts file>

The most basic statistics of the counts file, including:

- number of samples
- number of rows

Example JSON output::

    {
      'name': 'base',
      'stats': {
        'num_cols': 50,
        'num_rows': 27143
      }
    }

.. _coldist:

``coldist`` - Column-wise distribution of counts
-------------------------------------------------

Usage::

  detk-stats [options] coldist [--bins=<bins>] [--log] [--density] <counts file>

  Options:
    --bins=<bins>    The number of bins to use when computing the counts
                     distribution
    --log            Perform a log10 transform on the counts before calculating
                     the distribution. Zeros are omitted prior to histogram
                     calculation.
    --density        Return a density distribution instead of counts, such that
                     the sum of values in *dist* for each column approximately
                     sum to 1.

Compute the distribution of counts column-wise. Each column is subject
to binning by percentile, with output identical to that produced by
numpy.histogram_.

.. _numpy.histogram: https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html

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

In the *stats* object, the fields are defined as follows:

pct
  The percentiles of the distributions in the range 0 < pct < 100, by default
  in increments of 5. This defines the length of the *dist* and *bins*
  arrays in each of the objects for each sample.
dists
  Array of objects containing one object for each column, described below.


Each item of *dists* is an object with the following keys:

name
  Column name from original file
dist
  Array of raw or normalized counts in each bin according to the percentiles
  from *pct*
bins
  Array of the bin boundary values for the distribution.  Should be of length
  len(counts)+1. These are what would be the x-axis labels if this was
  plotted as a histogram.
extrema
  Object with two keys, *min* and *max*, that contain the literal count values
  for counts that have a value larger or smaller than 1.5*(inner quartile
  length) of the distribution. These could be marked as outliers in a boxplot,
  for example.


.. _rowdist:

``rowdist`` - Row-wise distribution of counts
---------------------------------------------

Usage::

  detk-stats [options] rowdist [--bins=<bins>] [--log] [--density] <counts file>

Identical to ``coldist`` except calculated across rows. The *name* key is
*rowdist*, and the *name* key of the items in *dists* is the row name from the
counts file.

.. _colzero:

``colzero`` - Column-wise distribution of zero counts
-----------------------------------------------------

Usage::

  detk-stats [options] colzero <counts fn>

Compute the number and fraction of exact zero counts for each column. Example
JSON output::

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

The *stats* value is an array containing one object per column as follows:

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

.. _rowzero:

``rowzero`` - Row-wise distribution of zero counts
--------------------------------------------------

Usage::

  detk-stats [options] rowzero <counts fn>

Identical to ``colzero``, only computed across rows instead of columns.  The
*name* key is *rowzero*, and the *name* key of the items in *dists* is the
row name from the counts file.

.. _entropy:

``entropy`` - Row-wise sample entropy calculation
-------------------------------------------------

Usage::

  detk-stats [options] entropy <counts fn>

Sample entropy is a metric that can be used to identify outlier samples by
locating rows which are overly influenced by a single count value. This metric
can be calculated for a single row as follows:

.. math::

  p_i = \frac{c_i}{\sum_j c_j}

  \sum p_i = 1

  H = - \sum_i p_i \log_2 p_i

Here, :math:`c_i` is the number of counts in sample :math:`i`, :math:`p_i` is
the fraction of reads contributed by sample :math:`i` to the overall counts
of the row, and :math:`H` is the `Shannon entropy`__ of the row when using
:math:`\log_2`. The maximum value possible for :math:`H` is 2 when using
Shannon entropy.

.. _shannon: https://en.wikipedia.org/wiki/Entropy_(information_theory)

__ shannon_

Rows with a very low :math:`H` indicate a row has most of its count mass
contained in a small number of columns. These are rows that are likely to
drive outliers in downstream analysis, e.g. differential expression.

Example JSON output::

  [
    'name': 'entropy',
    'stats': {
      'entropies': [
        {
          'name': 'row1',
          'entropy': 1.013
        },
        {
          'name': 'row2',
          'entropy': 0.001
        }
      ]
    }
  ]

The key *entropies* is an array containing one object per row with the
following keys:

name
  row name from counts file
entropy
  the value of :math:`H` calculated as above for that row

.. _pca:

``pca`` - Principal Component Analysis
--------------------------------------

This module performs Principal Component Analysis (PCA) on a :math:`n \times m`
counts matrix, where :math:`n` is the number of rows (genes) and :math:`m` is
the number of columns (samples).  Briefly, PCA identifies the directions (e.g.
genes and their magnitudes) that represent directions of maximal variance in a
dataset.  The output of PCA is a set of principal components, where each
principal component consists of an :math:`m`-length vector of *weights* or
*loadings* and a :math:`n`-length vector of *scores*. Each principal component
describes a precentage of the overall variance of the dataset. There are exactly
:math:`m` principal components identified by a PCA, but typically only a small
subset of these components explains a large amount of the variance in a real
dataset.

This module performs PCA on a provided counts matrix and returns the principal
component weights, scores, and variances. In addition, the weights and scores
for each individual component can be combined to define the *projection* of
each sample along that component. Commonly, projections of each sample against
each principal component can be used to identify outlier samples, batch effects,
sample group, etc by describing how each sample contributes to the variance in
each component. Therefore, the projections for each sample for each component
are also included in the output.

*Experimental:* The PCA module can also accept a metadata file that contains
information about the samples in each column. The user can specify some of these
columns to include as variables for plotting purposes. The idea is that columns
labeled with the same class will be colored according to their class, such that
separations in the data can be more easily observed when projections are
plotted.

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
          'weights': [1.013,0.352,...], # length m
          'scores': [0.126,0.975,...], # length n
          'projections': [-8.01,5.93,...], # length m, ordered by 'column_names'
          'perc_variance': 0.75
        },
        {
          'name': 'PC2',
          'weights': [1.013,0.352,...], # length m
          'scores' : [0.126,0.975,...], # length n
          'projections': [5.93,-5.11,...], # length m
          'perc_variance': 0.22
        }
      ]
    }
  ]

The html output for this module contains three plots: a `scree plot`__, a set
of line plots containing the sample projections, and an interactive scatter
plot where the user can choose which principal component projections to plot on
the X and Y axis. The two types of projection plots also have interactivity
allowing the user to select which column variable to use for coloring the
plotted projection points.

.. _scree_plot: http://www.improvedoutcomes.com/docs/WebSiteDocs/PCA/Creating_a_Scree_Plot.htm

__ scree_plot_
