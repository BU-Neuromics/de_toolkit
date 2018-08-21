Performing Differential Expression
==================================

Firth Logistic Expression
-------------------------

After normalization, differential expression can be performed. Currently only Firth's Logistic
Regression is implemented. Firth Logistic Regression requires three values. A design which specifies condition and covariates of interest in this form

**Without Covariates**::

  "Condition[VAR] ~ counts"


Alternatively covariates can be specified by adding them before ``counts`` separated by a ``+``. 

**With Covariates**::

  "Codition[VAR] ~ COV1+COV2+COVN+counts"


**Example**::

  detk-de firth "Codition[VAR] ~ COV1+COV2+COVN+counts" MyNormalizedCounts MyInfoFile -o MyDifferentialExpression

*Note*:

A tsv file is created when specifying output with ``-o``
