'''
Usage:
    detk-stats [options] summary [--bins=<bins>] [--log] [--density][--column-data=<column data fn>] [--color-col=<column_variable>] <counts_fn>
    detk-stats [options] base <counts_fn>
    detk-stats [options] coldist [--bins=<bins>] [--log] [--density] <counts_fn>
    detk-stats [options] rowdist [--bins=<bins>] [--log] [--density] <counts_fn>
    detk-stats [options] colzero <counts_fn>
    detk-stats [options] rowzero <counts_fn>
    detk-stats [options] entropy <counts_fn>
    detk-stats [options] pca [--column-data=<column data fn>] [--color-col=<column_variable>] <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --json=<json_fn>       Name of JSON output file
    --html=<html_fn>       Name of HTML output file

Description:
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

'''
import json
import math
import argparse
from collections import OrderedDict
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas
from docopt import docopt
from .common import *
import os.path
from sklearn.decomposition import PCA
from string import Template
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale
import mpld3
import seaborn as sns
import csv
import matplotlib.patches as ptches
import pkg_resources

def summary(count_mat, bins, log, density, metadata='') :
    '''
        Compute summary statistics on a counts matrix file
            detk-stats [--json=<json_fn>] [--html=<html_fn>] summary <counts file>

        This command is equivalent to running each of the following stats commands:
            base
            coldist
            rowdist
            colzero
            rowzero
            entropy
            pca
        and concatenating the results.
    '''

    total_output = []
    total_output.append(base(count_mat))
    total_output.append(coldist(count_mat, bins, log, density))
    total_output.append(rowdist(count_mat, bins, log, density))
    total_output.append(colzero(count_mat))
    total_output.append(rowzero(count_mat))
    total_output.append(entropy(count_mat))
    total_output.append(count_PCA(count_mat, metadata))

    return total_output

def base(count_mat) :
    '''
        Basic statistics of the counts file

        Usage: detk-stats base <counts file>
        

        The most basic statistics of the counts file, including:
            number of samples
            number of rows
    '''

    #Get counts, number of columns, and number of rows
    cnts = count_mat.counts.values
    num_cols=len(cnts[0])
    num_rows=len(cnts)

    #Format output
    output = {}
    output['name'] = 'base'
    output['stats'] = {}
    output['stats']['num_cols'] = num_cols
    output['stats']['num_rows'] = num_rows

    #Return output
    return output

def coldist(count_mat, b, log, density) :
    '''
        Column-wise distribution of counts

        Usage: detk-stats [options] coldist [--bins=<bins>] [--log] [--density] <counts file>

        Options:
              --bins=<bins>   The number of bins to use when computing the counts
                               distribution
              --log           Perform a log10 transform on the counts before calculating
                               the distribution. Zeros are omitted prior to histogram
                               calculation.
              --density       Return a density distribution instead of counts, such that
                               the sum of values in *dist* for each column approximately
                               sum to 1.
        
        Compute the distribution of counts column-wise. Each column is subject to binning by percentile,
        with output identical to that produced by numpy.histogram.

        In the stats object, the fields are defined as follows:
            pct
                The percentiles of the distributions in the range 0 < pct < 100, by default in
                increments of 5. This defines the length of the dist and bins arrays in each of
                the objects for each sample.
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
    '''
    #Format output
    output = {}
    output['name'] = 'coldist'
    output['stats'] = {}
    output['stats']['pct'] = list(range(5, 100, 5))

    output['stats']['dists'] = []

    for s in count_mat.sample_names:
        #to access the data in each column
        data = getattr(count_mat.counts,s).tolist()
        
        #Take the log10 of each count if log option is specified
        if log == 1:
            data=list(filter(lambda a: a != 0.0, data))
            data=np.log10(data)
        
     #for the upper and lower outliers
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR =  np.percentile(data, 75) - np.percentile(data, 25)

        #for the histogram bin edges and count numbers
        if density == 1:
            (n, bins, patches) = plt.hist(data, bins=b, label='hst', weights=np.zeros_like(np.asarray(data)) + 1. / np.asarray(data).size)
        else:
            (n, bins, patches) = plt.hist(data, bins=b, label='hst')

        #make the dict for each sample
        output['stats']['dists'].append({'name':s, 'dist':list(n), 'bins':list(bins)[1:],'extrema':{'lower':[i for i in data if i < Q1-1.5*IQR], 'upper':[i for i in data if i > Q3+1.5*IQR]}})

    return output


def rowdist(count_mat, b, log, density) :
    '''
        Row-wise distribution of counts
        
        Usage: detk-stats [options] rowdist [--bins=<bins>] [--log] [--density] <counts file>

        Identical to coldist except calculated across rows. The name key is rowdist, and the
        name key of the items in dists is the row name from the counts file.
    '''
    #Format output
    output = {}
    output['name'] = 'rowdist'
    output['stats'] = {}
    output['stats']['pct'] = list(range(5, 100, 5))

    output['stats']['dists'] = []
    
    for i in range(len(count_mat.feature_names)):
        #to access the data in each row
        data = count_mat.counts.iloc[i].tolist()

        #Compute log10 of each count if log option is specified
        if log==1:
            data=list(filter(lambda a: a != 0.0, data))
            data=np.log10(data)
        
        #for the upper and lower outliers
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR =  np.percentile(data, 75) - np.percentile(data, 25)

        #for the histogram bin edges and count numbers
        if density == 1:
            (n, bins, patches) = plt.hist(data, bins=b, label='hist',  weights=np.zeros_like(np.asarray(data)) + 1. / np.asarray(data).size)
        else:
            (n, bins, patches) = plt.hist(data, bins=b, label='hst')

        #make the dict for each row
        output['stats']['dists'].append({'name':count_mat.feature_names[i], 'dist':list(n), 'bins':list(bins)[1:],'extrema':{'lower':[i for i in data if i < Q1-1.5*IQR], 'upper':[i for i in data if i > Q3+1.5*IQR]}})

    return output



def colzero(count_mat) :
    '''
        Column-wise distribution of zero counts
    
        Usage: detk-stats [options] colzero <counts fn>

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
    '''

    #Get counts, number of columns, number of rows, and sample names
    cnts = count_mat.counts.values
    num_cols=len(cnts[0])
    num_rows=len(cnts)
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
    
    #Format output
    output = {}
    output['name'] = 'colzero'
    output['stats'] = {}
    output['stats']['zeros'] = []

    for i in range(0, num_cols):
        col = {}
        col['name'] = col_names[i]
        col['zero_count'] = zero_counts[i]
        col['zero_frac'] = zero_fracs[i]
        col['mean'] = col_means[i]
        col['nonzero_mean'] = nonzero_col_means[i]
        output['stats']['zeros'].append(col)

    #Return output
    return output

def rowzero(count_mat) :
    '''
        Row-wise distribution of zero counts
    
        Usage: detk-stats [options] rowzero <counts fn>

        Identical to colzero, only computed across rows instead of columns. The name 
        key is rowzero, and the name key of the items in dists is the row name from 
        the counts file.
    '''

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

    #Format output
    output = {}
    output['name'] = 'rowzero'
    output['stats'] = {}
    output['stats']['zeros'] = []

    for i in range(0, num_rows):
        row = {}
        row['name'] = row_names[i]
        row['zero_count'] = zero_counts[i]
        row['zero_frac'] = zero_fracs[i]
        row['mean'] = row_means[i]
        row['nonzero_mean'] = nonzero_row_means[i]
        output['stats']['zeros'].append(row)
    
    #Return output
    return output

def entropy(count_mat) :
    '''
        Row-wise sample entropy calculation
    
        Usage: detk-stats [options] entropy <counts fn>

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
    '''

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
    output = {}
    output['name'] = 'entropy'
    output['stats'] = {}
    output['stats']['entropies'] = []

    for i in range(0, num_rows):
        row = {}
        row['name'] = row_names[i]
        row['entropy'] = entropies[i]
        output['stats']['entropies'].append(row)

    #Return output
    return output

def count_PCA(count_mat, metadata=''):
    '''
    Principal common analysis of the counts matrix.

    Usage: detk-stats [options] pca [--m <column data fn>] [--f <column_variable>] <counts fn>

    This module performs PCA on a provided counts matrix and returns the principal component 
    weights, scores, and variances. In addition, the weights and scores for each individual 
    component can be combined to define the projection of each sample along that component.

    The PCA module can also accept a metadata file that contains information about the 
    samples in each column. The user can specify some of these columns to include as 
    variables for plotting purposes. The idea is that columns labeled with the same class 
    will be colored according to their class, such that separations in the data can be 
    more easily observed when projections are plotted.
    '''
    
    #Get counts from file and scale counts
    cnts = count_mat.counts.values

    cnts = scale(cnts)

    #Perform PCA and fit to the data
    pca = PCA()
    pca.fit(cnts)
    X = pca.transform(cnts)

    #Get sample names
    sample_names = list(count_mat.sample_names)

    #If metadata option is given, get column variables
    if metadata != '':
      m = open(metadata, 'r')
      s = csv.Sniffer()
      delim = s.sniff(m.read()).delimiter
      m.seek(0)
      df = pandas.read_csv(m, sep=delim)

      column_names = list(df)
      column_variables = [[] for i in range(0, len(column_names)-1)]

      for name in sample_names:
        row = df[df[column_names[0]] == name]
        for i in range(1, len(column_names)):
          column_variables[i-1].append(row.iloc[0][column_names[i]])
    
    #If metadata option is not given, column variables are empty lists
    else:
      column_names = []
      column_variables = []

    #Format output
    output = {}
    output['name'] = 'pca'
    output['stats'] = {}
    output['stats']['column_names'] = sample_names
    output['stats']['column_variables'] = {}
    output['components'] = []
    for i in range(1, len(column_names)):
      output['stats']['column_variables'][column_names[i]] = column_variables[i-1]
    for i in range(0, pca.n_components_):
        comp = {}
        comp['name'] = 'PC' + str(i+1)
        comp['scores'] = [row[i] for row in X]
        comp['projections'] = [row[i] for row in pca.components_]
        comp['perc_variance'] =  pca.explained_variance_ratio_[i]
        output['components'].append(comp)
    return output

def format_json(filename, output):

    # new dict for holding stats recs
    output_dict = OrderedDict()

    # see if filename already exists
    if os.path.isfile(filename) :
      # read in the existing file
      previous_output = []
      with open(filename) as f :
        for line in f:
          previous_output.append(json.loads(line))
        for d in previous_output :
          if 'name' not in d :
            raise Exception('Malformed detk-stats JSON record in pre-existing '
            'file, no name key:',str(d))
          output_dict[d['name']] = d

    # go through the given output and update output_dict appropriately
    if 'name' not in output :
      raise Exception('Malformed detk-stats JSON record in output '
        'file, no name key:',str(output))

    output_dict[output['name']] = output

    # write out values in output_dict
    with open(filename,'w') as f :
      for value in output_dict.values():
        json.dump(value,f)
        f.write('\n')

def format_html(html_fn, json_fn, counts_obj, color_col):

    #HTML template that will be filled in using the available JSON data
    resource = pkg_resources.resource_string(__name__, 'html_template.html')
    resource = resource.decode('utf-8')
    s = Template(resource)

    output_dict = OrderedDict()
    output = []
    with open(json_fn) as f:
        for line in f:
            output.append(json.loads(line))
        for d in output:
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
        pca_output = output_dict['pca']
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

        stats = pca_output.get('stats')
        column_variables = stats.get('column_variables')
        if color_col == '' and len(column_variables)!=0: 
            color_col = list(column_variables)[0]
       
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
        ax = sns.swarmplot(x='Principle Components', y='Projection', data=df, hue=color_col, palette=sns.color_palette(palette_colors))
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

def main(argv=None):

    #Create commandline arguments to pass in data files and selected method
    args = docopt(__doc__,argv=argv)
    
    #Create CountMatrix object from given data
    args['<counts_fn>'] = args.get('<counts_fn>')
    counts_obj = CountMatrixFile(args['<counts_fn>'])
 
   #If bin option is specified, set to given number (otherwise, default=20)
    args['--bins'] = args.get('--bins')
    if args['--bins'] is None:
        args['--bins'] = 20
    else:
        args['--bins'] = int(args['--bins'])

    #Set log option
    args['--log'] = args.get('--log')
 
   #Set density option
    args['--density'] = args.get('--density')

   #Get metadata if provided
    args['--column-data'] = args.get('--column-data')
    if args['--column-data'] is None:
        args['--column-data'] = ''

   #Get column variable to color pca plots by if provided
    args['--color-col'] = args.get('--color-col')
    if args['--color-col'] is None:
        args['--color-col'] = ''

    if args['pca'] :
        output = count_PCA(counts_obj, metadata=args['--column-data'])
    elif args['summary'] :
        output = summary(counts_obj
          ,args['--bins']
          ,args['--log']
          ,args['--density']
          ,metadata=args['--column-data']
        )
    elif args['coldist'] :
        output = coldist(counts_obj
          ,args['--bins']
          ,args['--log']
          ,args['--density']
        )
    elif args['rowdist'] :
        output = rowdist(counts_obj
          ,args['--bins']
          ,args['--log']
          ,args['--density']
        )
    elif args['colzero'] :
      output = colzero(counts_obj)
    elif args['rowzero'] :
      output = rowzero(counts_obj)
    elif args['entropy'] :
      output = entropy(counts_obj)
    elif args['base']:
      output = base(counts_obj)

    #Obtain string used to name output files, unless filename is specified
    filename_prefix = os.path.splitext(args['<counts_fn>'])

    #Check if JSON file option was specified
    json_fn = args.get('--json')
    if json_fn is None:
        json_fn = filename_prefix[0]+'.json'    

    #Format JSON output file
    if args['summary']:
        with open(json_fn,'w') as f:
            for item in output:
                json.dump(item,f)
                f.write('\n')
    else:
        format_json(json_fn ,output)

    # determine the html filename
    html_fn = args.get('--html')
    if html_fn is None:
        html_fn = filename_prefix[0]+'.html'

    # if user specified no html fn, or html_fn != 'None', then we are
    # writing out an html file
    
    if html_fn != 'None' :
        format_html(html_fn, json_fn, counts_obj, args['--color-col'])
    

if __name__ == '__main__':
    main()
