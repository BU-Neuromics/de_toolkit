r'''
Usage:
    detk-norm deseq2 [options] <counts_fn>
    detk-norm library [options] <counts_fn>
    detk-norm fpkm [options] <counts_fn> <lengths_fn>
Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
'''

todo = r'''
    detk-norm custom <counts_fn>
'''
cmd_opts = {
        'deseq2':r'''
Perform counts normalization on the given counts matrix using the method
implemented in the DESeq2 package.

Usage:
    detk-norm deseq2 [options] <counts_fn>

Options:
    -h --help                    Print out this help
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
    --size-factors=FILE          Write out the size factors found by the DESeq2
                                 method to two column tab separated file where
                                 the first column is sample name and the second
                                 column is the size factor
''',
    'library':r'''
Perform library size normalization on the columns of the given counts matrix.
Counts in each column are divided by the sum of each column.

Usage:
    detk-norm library [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
''',
    'fpkm':r'''
Perform Fragments Per Kilobase per Million normalization on the given counts
file. <lengths_fn> should be a delimited file with two columns, the first
being the name of one of the rows in the counts file and the second is the
effective length of the gene/sequence/etc to use in the normalization.

*Note:* Program will throw an error and exit if there are genes/sequences
in the counts file that are not found in the lengths file.

The order of names in the counts and lengths files do *not* have to be the
same.

Usage:
    detk-norm fpkm [options] <counts_fn> <lengths_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]

'''
}
from docopt import docopt
import sys, os
import numpy as np
import pandas
from .common import CountMatrixFile, DetkModule, _cli_doc
from .report import DetkReport
from .util import stub
from .wrapr import require_r, wrapr

class NormalizationException(Exception) : pass

# DESeq2 v1.14.1 uses this R code for normalization
#function (counts, locfunc = stats::median, geoMeans, controlGenes) 
#{
#        if (missing(geoMeans)) {
#                loggeomeans <- rowMeans(log(counts))
#        }
#        else {
#                if (length(geoMeans) != nrow(counts)) {
#                        stop("geoMeans should be as long as the number of rows of counts")
#                }
#                loggeomeans <- log(geoMeans)
#        }
#        if (all(is.infinite(loggeomeans))) {
#                stop("every gene contains at least one zero, cannot compute log geometric means")
#        }
#        sf <- if (missing(controlGenes)) {
#                apply(counts, 2, function(cnts) {
#                        exp(locfunc((log(cnts) - loggeomeans)[is.finite(loggeomeans) & 
#                                cnts > 0]))
#                })
#        }
#        else {
#                if (!(is.numeric(controlGenes) | is.logical(controlGenes))) {
#                        stop("controlGenes should be either a numeric or logical vector")
#                }
#                loggeomeansSub <- loggeomeans[controlGenes]
#                apply(counts[controlGenes, , drop = FALSE], 2, function(cnts) {
#                        exp(locfunc((log(cnts) - loggeomeansSub)[is.finite(loggeomeansSub) & 
#                                cnts > 0]))
#                })
#        }
#        sf
#}


def estimateSizeFactors(cnts):

    loggeomeans = np.log(cnts).mean(axis=1)
    if all(~np.isfinite(loggeomeans)) :
        raise NormalizationException(
         'every gene contains at least one zero, cannot compute log geometric means'
        )

    divFact = (np.log(cnts).T - loggeomeans).T
    sizeFactors = np.exp(
        np.apply_along_axis(
            lambda c: np.median(c[np.isfinite(c)])
            ,0
            ,divFact
        )
    )

    return sizeFactors

@require_r('DESeq2')
def estimateSizeFactors_wrapr(cnts):

    script = '''\
    library(DESeq2)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1))
    colData <- data.frame(name=seq(ncol(cnts)))
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = ~ 1)
    dds <- estimateSizeFactors(dds)
    write.csv(sizeFactors(dds),out.fn)
    '''

    with wrapr(script,
            counts=pandas.DataFrame(cnts),
            raise_on_error=False) as r :
        deseq2_size_factors = r.output['x'].values

    return list(deseq2_size_factors)

def deseq2(count_obj):
    obj = DESeq2Norm(count_obj)
    return obj.output

@require_r('DESeq2')
def deseq2_wrapr(count_obj):

    script = '''\
    library(DESeq2)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1))
    colData <- read.csv(metadata.fn,row.names=1)
    str(params$design)
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = formula(params$design))
    dds <- estimateSizeFactors(dds)
    write.csv(counts(dds,normalized=TRUE),out.fn,row.names=TRUE)
    '''

    # we need to get rid of the counts from the left hand side and the Intercept
    # from the right, otherwise the model matrix is not full rank and DESeq2
    # whines, whines!
    count_obj.design_matrix.drop_from_lhs('counts')
    count_obj.design_matrix.drop_from_rhs('Intercept')

    with wrapr(script,
            counts=count_obj.counts,
            metadata=count_obj.design_matrix.full_matrix,
            params={'design':count_obj.design},
            raise_on_error=True) as r :
        norm_counts = r.output.values

    return norm_counts

class DESeq2Norm(DetkModule):
    @require_r('DESeq2')
    def __init__(self, count_obj):
        count_mat = count_obj.counts.values
        sizeFactors = estimateSizeFactors(count_mat)
        norm_cnts = count_mat/sizeFactors
        normalized = pandas.DataFrame(norm_cnts, 
                index=count_obj.counts.index,
                columns=count_obj.counts.columns
                )
        self.normalized = normalized

    @property
    def output(self):
        return self.normalized
    @property
    def properties(self):
        return {'num_kept': len(self.normalized)
                }

def library_size(count_df,sizes=None):
    '''
    Divide each count by column sum
    '''
    obj = LibrarySize(count_df, sizes)
    return obj.output

class LibrarySize(DetkModule):
    def __init__(self, count_df, sizes):
        self['params'] = {'sizes': sizes}
        self.count_df = count_df
        self.librarysize = count_df / count_df.sum(axis=0)

    @property
    def output(self):
        return self.librarysize

    @property
    def properties(self):
        return {'num library size': len(self.librarysize)}

def fpkm(count_df,lengths) :
    '''
    Calculate Fragments Per Kilobase per Million reads

    *lengths* should be a pandas.Series object that has an index value for
    every row name in the counts matrix. If no length is found for a row in the
    counts matrix, an exception is raised.
    '''
    obj = FPKMCounts(count_df, lengths)
    return obj.output

class FPKMCounts(DetkModule):
    def __init__(self, count_df, lengths):
        self['params'] = {'lengths': lengths}
        self.count_df = count_df

        missing_indices = count_df.index.difference(lengths.index)
        if len(missing_indices) != 0 :
            raise NormalizationException(
                    '{} indices in the counts matrix were '.format(len(missing_indices))+
                    'not found in the lengths parameters, here are a couple: \n'+
                    '\n'.join(_ for _ in list(missing_indices)[:5])
                    )
        lens = lengths[count_df.index]
        res = count_df.div(1e6*lens,axis=0)
        self.res = res
    
    @property
    def output(self):
        return self.res
    @property
    def properties(self):
        return {'num_kept': len(self.res),
                'lengths': lengths
                }

@stub
def custom_norm(count_mat,factors) :
    pass

def main(argv=sys.argv) :

    if '--version' in argv :
        from .version import __version__
        print(__version__)
        return

    # add the common opts to the docopt strings
    cmd_opts_aug = {}
    for k,v in cmd_opts.items() :
        cmd_opts_aug[k] = _cli_doc(v)

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts) :
        docopt(_cli_doc(__doc__),argv)
    argv = argv[1:]
    cmd = argv[0]

    if cmd == 'deseq2' :
        args = docopt(cmd_opts_aug['deseq2'],argv)
        count_obj = CountMatrixFile(args['<counts_fn>'])
        out = DESeq2Norm(count_obj)
    elif cmd == 'library' :
        args = docopt(cmd_opts_aug['library'],argv)
        count_obj = CountMatrixFile(args['<counts_fn>'])
        out = LibrarySize(count_obj)
    elif cmd == 'fpkm' :
        args = docopt(cmd_opts_aug['fpkm'],argv)
        # the lengths_fn is assumed to be a file with two columns
        # ID<delim>int
        # providing the lengths that should be used for each ID in the counts
        # file
        lengths = pandas.read_table(args['<lengths_fn>'],sep=None)
        out = FPKMCounts(count_obj.counts,lengths)

    fp = sys.stdout if args['--output']=='stdout' else args['--output']
    out.output.to_csv(fp)
    
    with DetkReport(args['--report-dir']) as r :
        r.add_module(
                out,
                in_file_path=args['<counts_fn>'],
                out_file_path=args['--output'],
                column_data_path=args.get('--column-data'),
                workdir=os.getcwd()
                )


if __name__ == '__main__' :
    main()
