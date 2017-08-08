import numpy as np
from sklearn.decomposition import PCA
from sklearn import preprocessing
import pandas as pd
import sys
import os

fn = sys.argv[1]

#fn = os.path.abspath("all_salmon_norm.csv")

X = pd.read_csv(fn)

# To drop gene id which is usually in column[0]
cols = list(X)
cols = cols[1:]
X = X[cols]

X_row_mean = X.mean(axis=1)
X_row_std = X.std(axis=1)
X_scaled = (X.sub(X_row_mean,axis=0)).div(X_row_std,axis=0)
assert np.allclose(X_scaled.mean(axis=1),0)
assert np.allclose(X_scaled.std(axis=1),1)
print('X scaled shape: %s' % str(X_scaled.shape))

# Perform PCA
n_samples = len(X.index)
n_features = len(X.columns)
n_components = min(n_samples, n_features)
pca = PCA(n_components)
transformed = pca.fit_transform(X_scaled.T)

# The amount of variance explained by each of the selected components
print('Variance: %s' % str(pca.explained_variance_))
# Percentage of variance explained by each of the selected components
print('Variance ratio: %s' % str(pca.explained_variance_ratio_))
