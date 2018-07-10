'''
Usage:
    detk-de deseq2 [options] [--rda=RDA] <design> <count_fn> <cov_fn>
    detk-de firth [options] [--rda=RDA] <design> <count_fn> <cov_fn>
    detk-de t-test <count_fn> <cov_fn>

Options:
    -o FILE --output=FILE        Destination of primary output [default: stdout]
    --rda=RDA                                Filename passed to saveRDS() R function of the result
                                                     objects from the analysis
    --strict        Require that the sample order indicated by the column names in the
                            counts file are the same as, and in the same order as, the
                            sample order in the row names of the covariates file

'''
from docopt import docopt
import pandas
import sys
from .common import CountMatrixFile, InvalidDesignException
from .wrapr import (
        require_r, require_deseq2, wrapr, RExecutionError, RPackageMissing,
        require_r_package
    )
from .util import stub

@require_deseq2
def deseq2(count_obj) :
    pass

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
            applyf <- function(l,f) { mclapply(l,f,cores=params$cores) }
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

def main(argv=None) :

    args = docopt(__doc__,argv=argv)

    count_obj = CountMatrixFile(
        args['<count_fn>']
        ,args['<cov_fn>']
        ,design=args['<design>']
        ,strict=args.get('--strict',False)
    )

    if args['deseq2'] :
        deseq2(count_obj)
    elif args['firth'] :
        firth_out = firth_logistic_regression(count_obj,rda=args['--rda'])

        if args['--output'] == 'stdout' :
            f = sys.stdout
        else :
            f = args['--output']

        firth_out.to_csv(f,sep='\t')

if __name__ == '__main__' :

    main()
