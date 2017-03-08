import docopt
import pytest
from de_toolkit.transform import main

def test_transform_cli(fake_counts_csv) :
  with pytest.raises(docopt.DocoptExit) :
    main(argv=None)

def test_transform_vst_cli(fake_counts_csv):
  main(['vst',fake_counts_csv])
def test_transform_vst(fake_counts_csv):
  from de_toolkit.transform import vst
  pass

#def test_transform_ruvseq_cli(fake_counts_csv):
#  main(['ruvseq',fake_counts_csv])
#def test_transform_ruvseq(fake_counts_csv):
#  from de_toolkit.transform import ruvseq
#  pass

#def test_transform_trim_cli(fake_counts_csv):
#  main(['trim',fake_counts_csv])
#def test_transform_trim(fake_counts_csv):
#  from de_toolkit.transform import trim_outliers
#  pass

#def test_transform_shrink_cli(fake_counts_csv):
#  main(['shrink',fake_counts_csv])
#def test_transform_shrink(fake_counts) :
#  from de_toolkit.transform import shrink_outliers
#  pass
