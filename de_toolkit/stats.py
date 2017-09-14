import json
import math
import argparse
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas
from docopt import docopt
from .common import *
import os.path
from string import Template
from sklearn.decomposition import PCA

'''
Usage:
	detk-stats summary [options] <counts_fn>
	detk-stats base [options] <counts_fn>
	detk-stats coldist [options] [--bins=<bins>] [--log] [--density] <counts_fn>
	detk-stats rowdist [options] [--bins=<bins>] [--log] [--density] <counts_fn>
	detk-stats [options] colzero <counts fn>
	detk-stats [options] rowzero <counts fn>
	detk-stats [options] entropy <counts fn>

Options:
	-o FILE --output=FILE    Destination of primary output [default: stdout]
 	--json=<json_fn>	 Name of JSON output file
	--html=<html_fn> 	 Name of HTML output file

Description:
	Easy access to informative count matrix statistics. Each of these functions produces two outputs:

		a json formatted file containing relevant statistics in a machine-parsable format
		a human-friendly HTML page displaying the results
	
	All of the commands accept a single counts file as input with optional arguments as indicated in the
	documentation. By default, the JSON and HTML output files have the same basename without extension as
	the counts file but including .json or .html as appropriate. E.g., counts.csv will produce counts.json
	and counts.html in the current directory. These default filenames can be changed using optional command
	line arguments --json=<json fn> and --html=<html fn> as appropriate for all commands. If <json fn>,
	either default or specified, already exists, it is read in, parsed, and added to. The HTML report is
	overwritten on every invocation using the contents of the JSON file.

'''

def summary(count_mat, bins, log, density) :
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
		concatenating the results.
	'''

	total_output = []
	total_output.append(base(count_mat))
	total_output.append(coldist(count_mat, bins, log, density))
	total_output.append(rowdist(count_mat, bins, log, density))
	total_output.append(colzero(count_mat))
	total_output.append(rowzero(count_mat))
	total_output.append(entropy(count_mat))

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
	cnts = count_mat.counts.as_matrix()
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
	
	for i in range(len(count_mat.count_names)):
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
		output['stats']['dists'].append({'name':count_mat.count_names[i], 'dist':list(n), 'bins':list(bins)[1:],'extrema':{'lower':[i for i in data if i < Q1-1.5*IQR], 'upper':[i for i in data if i > Q3+1.5*IQR]}})

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
	cnts = count_mat.counts.as_matrix()
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
	cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)
	row_names = count_mat.count_names

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
		nonzero_row_means.append(sum(data)/(len(data)-data.count(0.0)))

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
	cnts = count_mat.counts.as_matrix()
	num_cols=len(cnts[0])
	num_rows=len(cnts)
	row_names = count_mat.count_names

	probs = []
	for i in range(len(row_names)):
		data = count_mat.counts.iloc[i].tolist()
		row_prob = []
		for item in data:
			row_prob.append(item/sum(data))
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

def count_PCA(count_mat):
    '''
    Principal common analysis of the counts matrix.
    Usage: detk-stats [options] PCA <counts fn>
    '''
    # To drop gene id which is usually in column[0]
    cnts = count_mat.counts.as_matrix()
    X = pandas.DataFrame(cnts)
    cols = list(X)
    cols = cols[1:]
    X = X[cols]

    # Calculate row mean and std to scale PCA to origin at 0
    X_row_mean = X.mean(axis=1)
    X_row_std = X.std(axis=1)
    X_scaled = (X.sub(X_row_mean,axis=0)).div(X_row_std,axis=0)
    assert np.allclose(X_scaled.mean(axis=1),0)
    assert np.allclose(X_scaled.std(axis=1),1)

    # Perform PCA
    n_samples = len(X.index)
    n_features = len(X.columns)
    n_components = min(n_samples, n_features)
    pca = PCA(n_components)
    transformed = pca.fit_transform(X_scaled.T)

    output = {}
    output['name'] = 'pca'
    output['stats'] = {}
    output['stats']['column_names'] = list(count_mat.sample_names)
#    output['stats']['column_variables'] = {}
#    output['stats']['column_variables']['sample_type'] = []
#    output['stats']['column_variables']['sample_batch'] = []
    output['components'] = []
    for i in range(len(cols)):
        comp = {}
        comp['name'] = 'PC' + str(i+1)
#        comp['scores'] = transformed (per gene)
#        comp['projections'] = transformed[:,i+1]
#        comp['perc_variance'] =  "variance"
        output['components'].append(comp)
    return output

def format_json(filename, method, output, funcs, counts_obj, funcs_present, log, density):
	final_output = []

	if os.path.isfile(filename):
		#If file does exist and stats for given method is already in it, rewrite stats
		if method in open(filename).read() and method != 'summary':
			print('Warning: ' + method + ' stats was already found in the output file and has been rewritten')
			final_output.append(output)
			
			#Rewrite other stats already present in the file as well
			for key in funcs:
				if key in open(filename).read() and key != method:
					chosen_func = funcs[key]

					#If coldist or rowdist are present, get number of bins
					if key == 'coldist' or key == 'rowdist':
						f = open(filename, 'r')
						for line in f:
							if key in line:
								json_output = json.loads(line)
								dists = json_output['stats']['dists']
								dist = dists[0]
								bins = dist['bins']
								b = len(bins)
						existing_output=chosen_func(counts_obj, b, log, density)
					else:
						existing_output = chosen_func(counts_obj)
					final_output.append(existing_output)
					funcs_present.append(key)
					print('Warning: ' + key + ' stats was already found in the output file and has been rewritten')

		#If file does exist but stats for the given method are not in it, add to that file
		elif method not in open(filename).read() and method != 'summary':
			json_fn = open(filename, 'a')
			json_fn.write(json.dumps(output) + '\n')
			json_fn.close()

			for key in funcs:
				if key in open(filename).read() and key != method:
					funcs_present.append(key)
			return

		#If summary method is specified, rewrite all stats
		else:
			for key in funcs:
				if key in open(filename).read():
					print('Warning: ' + key + ' stats was already found in the output file and has been rewritten')
				funcs_present.append(key)
			for item in output:
				final_output.append(item)

	#If output file is not present, create it and add the appropriate output
	else:
		final_output.append(output)

	#Write appropriate outputs to the JSON file
	json_fn = open(filename, 'w')
	for item in final_output:
		json_fn.write(json.dumps(item) + '\n')
	json_fn.close()

def format_html(filename, json_fn, funcs_present, counts_obj, log, density):
	#HTML template that will be filled in using the available JSON data
	html_temp = open('de_toolkit/html_template.html')
	s = Template(html_temp.read())

	#Format base HTML output (table)
	if 'base' in funcs_present:
		base_hide=''
		with open(json_fn) as file:
			for line in file:
				if 'base' in line:
					base_output = json.loads(line.strip('\n'))
		num_cols = base_output['stats']['num_cols']
		num_rows = base_output['stats']['num_rows']
	else:
		base_hide='hidden'
		num_cols=''
		num_rows=''

	#Format colzero HTML output (bar chart of samples and zero fractions)
	if 'colzero' in funcs_present:
		colzero_hide=''
		with open(json_fn) as file:
			for line in file:
				if 'colzero' in line:
					colzero_output = json.loads(line)
		zeros_list = colzero_output['stats']['zeros']
		colzero = "['Sample', 'Zero_Frac'],"
		for item in zeros_list:
			colzero+="['" + item['name'] + "', " + str(item['zero_frac']) + "],"
	else:
		colzero_hide='hidden'
		colzero=''

	#Format rowzero HTML output (scatterplot of zero fraction vs. nonzero mean and histogram of zero fracs)
	if 'rowzero' in funcs_present:
		rowzero_hide=''
		with open (json_fn) as file:
			for line in file:
				if 'rowzero' in line:
					rowzero_output = json.loads(line)
		zeros_list = rowzero_output['stats']['zeros']
		rowzero_scatter = "['Zero_frac', 'Nonzero_mean'],"
		rowzero_hist = "['Gene', 'Zero_frac'],"
		for item in zeros_list:
			rowzero_scatter+="[" + str(item['zero_frac']) + ", " + str(item['nonzero_mean']) + "],"
			rowzero_hist+="['" + item['name'] + "', " + str(item['zero_frac']) + "],"

	else:
		rowzero_hide='hidden'
		rowzero_scatter=''
		rowzero_hist=''

	#Format entropy HTML output (histogram)
	if 'entropy' in funcs_present:
		entropy_hide=''
		with open(json_fn) as file:
			for line in file:
				if 'entropy' in line:
					entropy_output = json.loads(line)
		entropies = entropy_output['stats']['entropies']
		entropy = "['Gene', 'Entropy'],"
		for item in entropies:
			entropy+="['" + item['name'] + "', " + str(item['entropy']) + "],"
	else:
		entropy_hide='hidden'
		entropy=''

	#Format coldist HTML output (box plots for each column)
	if 'coldist' in funcs_present:
		coldist_hide=''
		cnts = counts_obj.counts.as_matrix()
		with open(json_fn) as file:
			for line in file:
				if 'coldist' in line:
					coldist_output = json.loads(line)
		coldist_data=''
		dists = coldist_output['stats']['dists']
		col_sums = []
		for x in counts_obj.sample_names:
			data = getattr(counts_obj.counts,x).tolist()
			col_sums.append(sum(data))
		for i in range(0, len(dists)):
			coldist_data+="['" + dists[i]['name'] + "', "
			for j in range(0, len(cnts)):
				if density==1:
					coldist_data+= str(cnts[j][i]/col_sums[i]) + ","
				elif log==1:
					if cnts[j][i]!=0.0:
						coldist_data+= str(math.log10(cnts[j][i])) + ","
				else:
					coldist_data+= str(cnts[j][i]) + ","
			coldist_data+="],"
		coldist_cols=''
		for i in range(0, len(cnts)):
			coldist_cols+= "data.addColumn('number', 'series" + str(i) + "');" + "\n"

	else:
		coldist_hide = 'hidden'
		coldist_data = ''
		coldist_cols = ''

	#Write all outputs to HTML file
	html_output = s.safe_substitute(base_hide=base_hide, num_cols=num_cols, num_rows=num_rows,
                                        colzero_hide=colzero_hide, colzero=colzero,
                                        rowzero_hide=rowzero_hide, rowzero_scatter=rowzero_scatter, rowzero_hist=rowzero_hist,
                                        entropy_hide=entropy_hide, entropy=entropy,
					coldist_hide=coldist_hide, coldist_data=coldist_data, coldist_cols=coldist_cols)
	html_fn = open(filename, 'w')
	html_fn.write(html_output)
	html_fn.close()

def main():
	
	#Create commandline arguments to pass in data files and selected method
	parser = argparse.ArgumentParser()
	parser.add_argument("method",
		choices=['base', 'coldist', 'rowdist', 'colzero', 'rowzero', 'entropy', 'summary'],
		help="Choose one of the specified functions to be run")
	parser.add_argument("file", help="Name of input data file")
	parser.add_argument("--bins", help="The number of bins to use when computing the counts distribution for coldist or rowdist")
	parser.add_argument("--log", help="Perform a log10 transform on the counts before calculating the distribution for colzero or rowzero. Zeros are omitted prior to histogram calculation", action='store_const', const=1)
	parser.add_argument("--density", help="Return a density distribution instead of counts for coldist or rowdist", action='store_const', const=1)
	parser.add_argument("--json", help="Name of JSON output file")
	parser.add_argument("--html", help="Name of HTML output file")
	args = parser.parse_args()

	#Create CountMatrix object from given data
	counts_obj = CountMatrixFile(args.file)
	
	#Dictionary containing the methods that can be called
	funcs = {'base': base, 'coldist': coldist, 'rowdist': rowdist, 'colzero': colzero,
                'rowzero': rowzero, 'entropy':entropy, 'summary': summary}

	#Run specified method
	chosen_func = funcs[args.method]
	funcs_present = [args.method]

	#If bin option is specified, set to given number (otherwise, default=20)
	if args.bins:
		b = int(args.bins)
	else:
		b = 20

	#Set log option
	if args.log:
		log = 1
	else:
		log = -1

	#Set density option
	if args.density:
		density=1
	else:
		density=-1

	#If method is coldist, rowdist, or summary, run with base, log and density settings
	if args.method == 'coldist' or args.method=='rowdist' or args.method=='summary':
		output = chosen_func(counts_obj, b, log, density)
	
	#Otherwise, run method with just the counts object
	else:
		output = chosen_func(counts_obj)

	#Obtain string used to name output files, unless filename is specified
	index = args.file.rfind('.')
	file_str = args.file[:index]

	#Check if JSON file option was specified
	if args.json:
		filename=args.json
	else:
		filename=file_str+ '.json'

	#Format JSON output file
	format_json(filename, args.method, output, funcs, counts_obj, funcs_present, log, density)
	
	#Check if HTML file option was specified
	if args.html:
		html_fn = args.html
	else:
		html_fn = file_str + '.html'
	
	#Format HTML output file
	format_html(html_fn, filename, funcs_present, counts_obj, log, density)

if __name__ == '__main__':
	main()
