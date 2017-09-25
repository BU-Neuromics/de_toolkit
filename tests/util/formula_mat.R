library(logistf)

df <- data.frame(
  cont=runif(100),
  binary_bool=runif(100)>0.5,
  binary_int=as.integer(runif(100)>0.5),
  cat_str=unlist(lapply(runif(100),
    function(x) {
      if(x<0.25) { return('A') }
      else if(x<0.5) { return('B') }
      else if(x<0.75) { return('C') }
      else { return('D') }})
  ),
  cat_int=unlist(lapply(runif(100),function(x) { return(as.integer(x*10)) }))
)

# construct a numeric model matrix containing all the columns of the dataframe
# cont, binary_int, and cat_int are already numeric in the original df
# binary_bool and cat_str are interpreted as factors and expanded to dummy
# variables of the form varLEVEL, e.g. binary_boolTRUE, cat_strB, cat_strC, etc.
mm <- model.matrix(formula("~ cont + binary_int + binary_bool + cat_int + cat_str"),df)

# this model matrix can be passed directly to functions expecting a formula
# that includes explicitly the variables required
# the model matrix must be converted back to a data frame before many of these
# functions will accept it
mm.df <- as.data.frame(mm)

# these two calls should return equivalent results
explicit.mat.fit <- logistf(formula("binary_boolTRUE ~ cont + cat_strB + cat_strC + cat_strD"),mm.df)
implicit.mat.fit <- logistf(formula("binary_bool ~ cont + cat_str"),df)

str(explicit.mat.fit)
str(implicit.mat.fit)

stopifnot(all(explicit.mat.fit$coefficients == implicit.mat.fit$coefficients))

print("all coefficients are the same")
