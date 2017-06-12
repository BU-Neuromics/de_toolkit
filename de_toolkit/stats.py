import json
import math
from collections import OrderedDict
import argparse
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas
from docopt import docopt
from common import * 
import os.path
from string import Template

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

def summary(count_mat) :
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
	total_output.append(coldist(count_mat))
	total_output.append(rowdist(count_mat))
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
	base_output = OrderedDict([['num_cols', num_cols], ['num_rows', num_rows]])
	output = OrderedDict([['name', 'base'], ['stats', base_output]])

	#Return output
	return output

def coldist(count_mat) :
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
	output = {}
	output['name'] = 'coldist'
	output['stats'] = {}
	output['stats']['pct'] = list(range(5, 100, 5))

	output['stats']['dists'] = []
	for s in count_mat.sample_names:
        #to access the data in each column
		data = getattr(count_mat.counts,s).tolist()

        #for the upper and lower outliers
		Q1 = np.percentile(data, 25)
		Q3 = np.percentile(data, 75)
		IQR =  np.percentile(data, 75) - np.percentile(data, 25)

        #for the histogram bin edges and count numbers
		(n, bins, patches) = plt.hist(data, bins=20, label='hst')

        #make the dict for each sample
		output['stats']['dists'].append({'name':s, 'dist':list(n), 'bins':list(bins)[1:],'extrema':{'lower':[i for i in data if i < Q1-1.5*IQR], 'upper':[i for i in data if i > Q3+1.5*IQR]}})

	return output


def rowdist(count_mat) :
	'''
		Row-wise distribution of counts
		
		Usage: detk-stats [options] rowdist [--bins=<bins>] [--log] [--density] <counts file>

		Identical to coldist except calculated across rows. The name key is rowdist, and the 
		name key of the items in dists is the row name from the counts file.
	'''
	output = {}
	output['name'] = 'rowdist'
	output['stats'] = {}
	output['stats']['pct'] = list(range(5, 100, 5))

	output['stats']['dists'] = []
	for i in range(len(count_mat.count_names)):
        #to access the data in each row
		data = count_mat.counts.iloc[i].tolist()

        #for the upper and lower outliers
		Q1 = np.percentile(data, 25)
		Q3 = np.percentile(data, 75)
		IQR =  np.percentile(data, 75) - np.percentile(data, 25)

        #for the histogram bin edges and count numbers
		(n, bins, patches) = plt.hist(data, bins=20, label='hst')

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

	#Calculate zero counts for each column
	zero_counts =[]
	for i in range(0, num_cols):
		zero_count = 0
		for j in range(0, num_rows):
			if cnts[j][i]==0:
				zero_count+=1
		zero_counts.append(zero_count)

	#Calculate zero fractions for each column
	zero_fracs = []
	for i in range(0, num_cols):
		zero_frac=zero_counts[i]/num_rows
		zero_fracs.append(zero_frac)

	#Calculate means for each column
	col_means = []
	for i in range(0, num_cols):
		mean = 0.0
		for j in range(0, num_rows):
			mean+=cnts[j][i]
		mean=mean/num_rows
		col_means.append(mean)

	#Calculate the means of only the nonzero counts in each column
	nonzero_col_means = []
	for i in range(0, num_cols):
		mean=0.0
		num=0
		for j in range(0, num_rows):
			if cnts[j][i] != 0:
				mean+=cnts[j][i]
				num+=1
		if num != 0:
			mean=mean/num
		nonzero_col_means.append(mean)

	#Format output
	output = OrderedDict([['name', 'colzero'], ['stats', {}]])
	output['stats']['zeros'] = []

	for i in range(0, num_cols):
		col = OrderedDict([['name', col_names[i]],
		['zero_count', zero_counts[i]],
		['zero_frac', zero_fracs[i]],
		['mean', col_means[i]],
		['nonzero_mean', nonzero_col_means[i]]])

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

	#Calculate zero counts for each row
	zero_counts =[]
	for i in range(0, num_rows):
		zero_count = 0
		for j in range(0, num_cols):
			if cnts[i][j]==0:
				zero_count+=1
		zero_counts.append(zero_count)

	#Calculate zero fractions for each rows
	zero_fracs = []
	for i in range(0, num_rows):
		zero_frac=zero_counts[i]/num_cols
		zero_fracs.append(zero_frac)

	#Calculate means for each row
	row_means = []
	for i in range(0, num_rows):
		mean = 0.0
		for j in range(0, num_cols):
			mean+=cnts[i][j]
		mean=mean/num_cols
		row_means.append(mean)

	#Calculate the means of only the nonzero counts for each row
	nonzero_row_means = []
	for i in range(0, num_rows):
		mean = 0.0
		num = 0
		for j in range(0, num_cols):
			if cnts[i][j] != 0:
				mean+=cnts[i][j]
				num+=1
		if num != 0:
			mean=mean/num
		nonzero_row_means.append(mean)

	#Format output
	output = OrderedDict([['name', 'rowzero'], ['stats', {}]])
	output['stats']['zeros'] = []

	for i in range(0, num_rows):
		row = OrderedDict([['name', row_names[i]],
		['zero_count', zero_counts[i]],
		['zero_frac', zero_fracs[i]],
		['mean', row_means[i]],
		['nonzero_mean', nonzero_row_means[i]]])

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

	#Calculate probabilities for each count by row
	probs = []
	for i in range(0, num_rows):
		row_probs = []
		sum = 0.0
		for j in range(0, num_cols):
			sum+=cnts[i][j]
		for j in range(0, num_cols):
			row_probs.append(cnts[i][j]/sum)
		probs.append(row_probs)

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
	output = OrderedDict([['name', 'entropy'], ['stats', {}]])
	output['stats']['entropies'] = []

	for i in range(0, num_rows):
		row = OrderedDict([['name', row_names[i]],
		['entropy', entropies[i]]])

		output['stats']['entropies'].append(row)

	#Return output
	return output

def format_json(filename, method, output, funcs, counts_obj, funcs_present):
	final_output = []

	if os.path.isfile(filename):
		#If file does exist and stats for given method is already in it, rewrite stats
		if method in open(filename).read() and method != 'summary':
			print('Warning: ' + method + ' stats was already found in the output file and has been rewritten')
			final_output.append(output)
			
			for key in funcs:
				if key in open(filename).read() and key != method:
					chosen_func = funcs[key]
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
			final_output = output

	#If output file is not present, create it and add the appropriate output
	else:
		final_output.append(output)

	json_fn = open(filename, 'w')
	for item in final_output:
		json_fn.write(json.dumps(item) + '\n')
	json_fn.close()

def format_html(filename, json_fn, funcs_present, counts_obj):
	html_temp = open('de_toolkit/html_template.html')
	s = Template(html_temp.read())
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

	if 'coldist' in funcs_present:
		coldist_hide=''
		cnts = counts_obj.counts.as_matrix()
		with open(json_fn) as file:
			for line in file:
				if 'coldist' in line:
					coldist_output = json.loads(line)
		coldist_data=''
		dists = coldist_output['stats']['dists']
		for i in range(0, len(dists)):
			coldist_data+="['" + dists[i]['name'] + "', "
			for j in range(0, len(cnts)):
				coldist_data+= str(cnts[j][i]) + ","
			coldist_data+="],"
		coldist_cols=''
		for i in range(0, len(cnts)):
			coldist_cols+= "data.addColumn('number', 'series" + str(i) + "');" + "\n"

	else:
		coldist_hide = 'hidden'
		coldist_data = ''
		coldist_cols = ''

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
	parser.add_argument("cfile", help="Name of input column data file")
	parser.add_argument("file", help="Name of input data file")
	parser.add_argument("--json", help="Name of JSON output file")
	parser.add_argument("--html", help="Name of HTML output file")
	args = parser.parse_args()

	#Create CountMatrix object from given data
	counts_obj = CountMatrixFile(args.file, args.cfile, '~ category')
	
	#Dictionary containing the methods that can be called 
	funcs = {'base': base, 'coldist': coldist, 'rowdist': rowdist, 'colzero': colzero,
                'rowzero': rowzero, 'entropy':entropy, 'summary': summary}

	#Run specified method
	chosen_func = funcs[args.method]
	output = chosen_func(counts_obj)
	funcs_present = [args.method]

	#Obtain string used to name output files, unless filename is specified
	index = args.file.rfind('.')
	file_str = args.file[:index]

	#Check if JSON file option was specified
	if args.json:
		filename=args.json
	else:
		filename=file_str+ '.json'

	#Format JSON output file
	format_json(filename, args.method, output, funcs, counts_obj, funcs_present)
	
	#Check if HTML file option was specified
	if args.html:
		html_fn = args.html
	else:
		html_fn = file_str + '.html'
	
	#Format HTML output file
	format_html(html_fn, filename, funcs_present, counts_obj)

if __name__ == '__main__':
	main()
