import csv
import numpy as np
import pandas
import pytest
import tempfile

#fake_counts_text_data = pytest.fake_counts_text_data

def test_load_count_mat_file(fake_counts_csv, fake_counts_text_data) :

  from de_toolkit.util import load_count_mat_file

  #with tempfile.NamedTemporaryFile('wt',delete=False) as f :
#
#    tmp_f = csv.writer(f)
#    for r in fake_counts_text_data() :
#      tmp_f.writerow(r)

  count_obj = load_count_mat_file(fake_counts_csv)

  data = fake_counts_text_data
  data = pandas.DataFrame(data[1:],columns=data[0])
  data.index = data.gene
  del data['gene']
  data = data.apply(pandas.to_numeric)

  assert np.allclose(data.as_matrix(), count_obj.counts.as_matrix())
  assert all(data.columns == count_obj.sample_names)
  assert all(data.index == count_obj.count_names)

