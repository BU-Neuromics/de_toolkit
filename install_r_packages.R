packages <- c('logistf')
lapply(
  packages
  ,function(package) {
    install.packages(package, dependencies=TRUE, repos='http://cran.rstudio.com/')
  }
)
source('http://bioconductor.org/biocLite.R')
biocLite('DESEq2')
