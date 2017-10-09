# set the CRAN repo for the whole process so biocLite can also use it
r <- getOption('repos')
r['CRAN'] <- 'http://cran.rstudio.com/'
options(repos = r)

# standard R packages here
packages <- c('logistf')
lapply(
  packages
  ,function(package) {
    install.packages(package, dependencies=TRUE)
  }
)

# bioconductor packages here
source('http://bioconductor.org/biocLite.R')
biocLite('DESeq2')
