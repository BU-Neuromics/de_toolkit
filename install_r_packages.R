packages <- c('logistf')
lapply(
  packages
  ,function(package) {
    install.packages(package, dependencies=TRUE, repos='http://cran.rstudio.com/')
  }
)
