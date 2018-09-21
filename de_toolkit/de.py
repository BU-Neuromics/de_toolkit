'''\
Usage:
    detk-de deseq2 [options] <design> <count_fn> <cov_fn>
    detk-de firth [options] <design> <count_fn> <cov_fn>
'''

TODO = '''
    detk-de t-test ( help | [options] <count_fn> <cov_fn> )
'''

cmd_opts = {
        'deseq2':'''\
Usage:
    detk-de deseq2 [options] <design> <count_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
    --norm-counts          Prevent DESeq2 from normalizing counts prior to
                           running differential expression, default behavior
                           assumes that provided counts are raw
    --last-term-only       Use the default DESeq2 behavior of returning DE parameters
                           for the last term in the model, default behavior is to
                           report parameters for all variables in the model
    --gene-wise-disp       Use estimateDispersionsGeneEst instead of estimateDispersions
    --cores=N              Tell DESeq2 to use N cores when running, requires the
                           BiocParallel Bioconductor package to be installed [default: none]
''',
        'firth':'''\
Usage:
    detk-de firth [options] <design> <count_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
    --standardize          Standardize counts prior to running logistic regression
                           as to obtain standardized (i.e. directly comparable)
                           beta coefficients
    --cores=N              Tell R to use N cores when running, requires the
                           parallel R package to be installed [default: none]
'''
}

from docopt import docopt
import pandas
import sys
from .common import CountMatrixFile, InvalidDesignException
from .wrapr import (
        require_r, require_deseq2, wrapr, RExecutionError, RPackageMissing,
        require_r_package
    )
from .util import stub

@require_r('DESeq2')
def deseq2(
        count_obj,
        normalized=True,
        rda=None,
        all_coeff_results=True,
        gene_wise_disp_est=False,
        cores=None) :

    # make a copy of count_obj, since we mutate it
    count_obj = count_obj.copy()

    # validate the design matrix
    if count_obj.design is None or count_obj.design_matrix is None :
        raise InvalidDesignException('count_obj must have a design matrix to use'
            ' DESeq2')

    if 'counts' not in count_obj.design_matrix.lhs :
        raise InvalidDesignException('The term "counts" must exist on the left '
            ' hand side of the model in DESeq2')

    # drop the counts from the left hand side since DESeq2 doesn't use it
    count_obj.design_matrix.drop_from_lhs('counts',quiet=True)

    # make sure the rhs of the design matrix doesn't have an intercept
    count_obj.design_matrix.drop_from_rhs('Intercept',quiet=True)

    if cores is not None :
        require_r_package('BiocParallel')
        try :
            cores = int(cores)
        except ValueError :
            raise Exception('The cores argument to DESeq2 '
                    'must be an integer')

    params = {
        'design': count_obj.design,
        'normalized': normalized,
        'rda': rda,
        'cores': cores,
        'all.coeff.results': all_coeff_results,
        'gene.wise.disp.est': gene_wise_disp_est
    }
    script = '''\
        library(DESeq2)
        cnts <- read.csv(counts.fn,header=T,as.is=T)
        index.name <- names(cnts)[1]
        rownames(cnts) <- cnts[[1]]
        cnts <- cnts[c(-1)]

        rnames <- rownames(cnts)

        # DESeq2 whines when input counts aren't integers
        # round the counts matrix
        cnts <- data.frame(lapply(cnts,function(x) { round(as.numeric(x)) }))
        rownames(cnts) <- rnames

        # use parallelism if params$cores > 0
        cores <- if(is.null(params$cores)) { 0 } else { as.numeric(params$cores) }
        parallel <- FALSE
        if(cores>0) {
            library(BiocParallel)
            register(MulticoreParam(cores))
            parallel <- TRUE
        }

        # design formula
        form <- params$design

        # load design matrix
        design.mat <- read.csv(metadata.fn,header=T,as.is=T,row.names=1)

        dds <- DESeqDataSetFromMatrix(
            countData = cnts,
            colData = design.mat,
            design = formula(form)
        )

        # if counts are already normalized, don't normalize them
        if(params$normalized) {
            sizeFactors(dds) <- rep(1,nrow(design.mat))
        } else {
            dds <- estimateSizeFactors(dds)
        }

        # in some cases R can throw this error:
        if(params$gene.wise.disp.est) {
            dds <- estimateDispersionsGeneEst(dds)
            dispersions(dds) <- mcols(dds)$dispGeneEst
        } else {
            dds <- estimateDispersions(dds)
        }

        # turn off cooks distance outlier replacement
        #dds <- DESeq(dds,minReplicatesForReplace=Inf,parallel=parallel)

        dds <- nbinomWaldTest(dds)

        result_from_dds <- function(name) {
            res.df <- data.frame(
                log2FoldChange=mcols(dds)[[name]],
                lfcSE=mcols(dds)[[paste0('SE_',name)]],
                stat=mcols(dds)[[paste0('WaldStatistic_',name)]],
                pvalue=mcols(dds)[[paste0('WaldPvalue_',name)]],
                padj=p.adjust(mcols(dds)[[paste0('WaldPvalue_',name)]],method='fdr')
            )
            colnames(res.df) <- paste(name,colnames(res.df),sep='__')
            res.df
        }

        # organize output results
        res.df <- if(params$all.coeff.results==TRUE) {
            # report statistics and p-values on all model variables
            # output columns are:
            #   basemean
            #   for each model variable:
            #     <varname>__log2FoldChange (mcols(dds)[['<varname>']])
            #     <varname>__lfcSE (mcols(dds)[['SE_<varname>']])
            #     <varname>__stat (mcols(dds)[['WaldStatistic_<varname>']])
            #     <varname>__pvalue (mcols(dds)[['WaldPvalue_<varname>']])
            #     <varname>__padj (p.adjust(mcols(dds)[['WaldPvalue_<varname>']],method='fdr')

            # example mcols(dds) names:
            # Intercept
            # category__case
            # SE_Intercept
            # SE_category__case
            # WaldStatistic_Intercept
            # WaldStatistic_category__case
            # WaldPvalue_Intercept
            # WaldPvalue_category__case
            do.call(
                cbind,
                lapply(
                    colnames(design.mat),
                    result_from_dds
                )
            )
        } else {
            # just report the last column as is the DESeq2 default
            result_from_dds(tail(colnames(design.mat),n=1))
        }

        # add on the basemean
        res.df <- cbind(mcols(dds)[['baseMean']],res.df)
        colnames(res.df)[1] <- 'baseMean'

        if(!is.null(params$rda)) {
            saveRDS(dds,params$rda)
        }

        # because R is stupid and can't easily write out a column name for
        # a row name
        res.df.cols <- colnames(res.df)
        res.df[[index.name]] <- rnames
        res.df <- res.df[c(index.name,res.df.cols)]

        write.csv(res.df,out.fn,row.names=F)
    '''
    with wrapr(script,
            counts=count_obj.counts,
            metadata=count_obj.design_matrix.full_matrix,
            params=params) as wr :
        return wr.output

@require_r('logistf')
def firth_logistic_regression(
        count_obj,
        standardize=False,
        rda=None,
        cores=None) :

    # make a copy of count_obj, since we mutate it
    count_obj = count_obj.copy()

    # validate the design matrix
    if count_obj.design is None or count_obj.design_matrix is None :
        raise InvalidDesignException('count_obj must have a design matrix in Firth'
            ' logistic regression')

    if 'counts' not in count_obj.design_matrix.rhs :
        raise InvalidDesignException('The term "counts" must exist on the right hand'
            'side of the model in Firth logistic regression')

    # make sure the rhs of the design matrix doesn't have an intercept
    count_obj.design_matrix.drop_from_rhs('Intercept',quiet=True)

    if cores is not None :
        require_r_package('parallel')
        try :
            cores = int(cores)
        except ValueError :
            raise Exception('The cores argument to firth_logistic_regression '
                    'must be an integer')

    params = {
        'design': count_obj.design,
        'standardize': standardize,
        'rda': rda,
        'cores': cores
    }
    script = '''\
        library(logistf)
        cnts <- read.csv(counts.fn,header=T,as.is=T)
        index.name <- names(cnts)[1]
        rownames(cnts) <- cnts[[1]]
        cnts <- cnts[c(-1)]

        rnames <- rownames(cnts)
        cnts <- data.frame(lapply(cnts,as.numeric))
        rownames(cnts) <- rnames

        # scale counts to obtain standardized beta estimates
        if(params$standardize) {
            cnts <- data.frame(t(scale(t(cnts))))
        }

        # design formula
        form <- params$design

        # load design matrix
        design.mat <- read.csv(metadata.fn,header=T,as.is=T,row.names=1)

        fit <- NULL

        applyf <- lapply
        if(!is.null(params$cores)) {
            library(parallel)
            applyf <- function(l,f) { mclapply(l,f,mc.cores=params$cores) }
        }
        res.orig <- applyf(rownames(cnts),
            function(gene) {
              x <- data.frame(design.mat)
              x$counts <- unlist(cnts[gene,])
              log.fit <- logistf(formula(form),data=x,pl=F)
              fit <<- log.fit
              out <- c(gene, 'OK')
              names(out) <- c(index.name,'status')
              coeffs <- log.fit$coeff
              names(coeffs) <- paste0(names(coeffs),'__beta')
              probs <- log.fit$prob
              names(probs) <- paste0(names(probs),'__p')
              padj <- rep(NA,length(probs))
              names(padj) <- paste0(names(log.fit$prob),'__padj')
              cp <- c(rbind(coeffs,probs,padj))
              cp.names <- c(rbind(names(coeffs),names(probs),names(padj)))
              cp.names <- gsub(".Intercept.","int",cp.names)
              names(cp) <- cp.names
              c(out,cp)
            }
        )

        if(!is.null(params$rda)) {
            saveRDS(fit,params$rda)
        }
        res <- do.call(rbind,res.orig)
        res.df <- as.data.frame(res,stringsAsFactors=F)
        for(c in colnames(res.df)[c(-1,-2)]) {
            res.df[c] <- as.numeric(res.df[c][[1]])
        }
        # calculate p.adjust for each pvalue col
        for(c in Filter(function(x) endsWith(x,'__p'),colnames(res.df))) {
            res.df[paste0(c,'adj')] <- p.adjust(res.df[[c]],"fdr")
        }

        write.csv(res.df,out.fn,row.names=F)
    '''

    with wrapr(script,
            counts=count_obj.counts,
            metadata=count_obj.design_matrix.full_matrix,
            params=params) as wr :
        return wr.output

@stub
def t_test(count_obj) :
    pass

def main(argv=sys.argv) :

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts) :
        docopt(__doc__)
    argv = argv[1:]
    cmd = argv[0]

    if cmd == 'deseq2' :
        args = docopt(cmd_opts['deseq2'],argv)
        count_obj = CountMatrixFile(
            args['<count_fn>']
            ,args['<cov_fn>']
            ,design=args['<design>']
            ,strict=args.get('--strict',False)
        )

        out_df = deseq2(count_obj,
               normalized=args.get('--norm-counts',False),
               rda=args.get('--rda'),
               all_coeff_results=not args.get('--last-term-only',False),
               gene_wise_disp_est=args.get('--gene-wise-disp',False),
               cores=int(args['--cores']) if args['--cores'] != 'none' else None
        )

    elif cmd == 'firth' :
        args = docopt(cmd_opts['firth'],argv)
        count_obj = CountMatrixFile(
            args['<count_fn>']
            ,args['<cov_fn>']
            ,design=args['<design>']
            ,strict=args.get('--strict',False)
        )

        out_df = firth_logistic_regression(count_obj,
                rda=args['--rda'],
                standardize=args.get('--standardize',False),
                cores=int(args['--cores']) if args['--cores'] != 'none' else None
        )

    if args['--output'] == 'stdout' :
        f = sys.stdout
    else :
        f = args['--output']

    out_df.to_csv(f,sep='\t')

if __name__ == '__main__' :

    main()
