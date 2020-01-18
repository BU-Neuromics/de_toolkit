from collections import OrderedDict
import csv
import numpy as np
import pandas
import pytest
import os
import tempfile

from de_toolkit.wrapr import check_r, require_r, check_r_package

r_test = pytest.mark.skipif(not check_r(),
        reason='r is not installed, skipping test'
)
fgsea_test = pytest.mark.skipif(not check_r_package('fgsea'), 
        reason='fgsea package not installed, skipping test'
)

@pytest.fixture
def gset_dict(request):
    d = OrderedDict()
    d['set1'] = ['gene1','gene2','gene3']
    d['set2'] = ['gene1','gene4','gene5']
    d['set3'] = ['gene1','gene2','gene3','gene4','gene5']
    d['set4'] = ['gene6','gene7','gene8','gene9','gene10']
    d['set5'] = ['gene1','gene7','gene3','gene9','gene5']
    return d

@pytest.fixture()
def gmt_file(request,gset_dict) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter='\t')
    for name, ids in gset_dict.items() :
      tmp_f.writerow([name,name]+list(ids))

  yield f.name

  # cleanup the csv
  os.remove(f.name)

@pytest.fixture()
def gmt_file_w_unicode(request) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
    tmp_f = csv.writer(f,delimiter='\t')
    tmp_f.writerow(['set1','tgf\u03b1','gene1','gene2'])

  yield f.name

  # cleanup the csv
  os.remove(f.name)


@pytest.fixture()
def gmt_obj(request,gset_dict) :
    from de_toolkit.enrich import GMT
    return GMT(gset_dict)

@pytest.fixture()
def stat(request) :
    return pandas.Series(
        range(10),
        index=['gene{}'.format(_+1) for _ in range(10)]
    )

@pytest.fixture
def result_csv(request,stat) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
      df = pandas.DataFrame({
          'negstat':-stat.values,
          'nonsense':np.random.random(size=10),
          'stat':stat.values,
          'gene':stat.index.tolist()
          },
          index=stat.index
      )
      df.to_csv(f.name,index_label='id')

  yield f.name

  # cleanup the csv
  os.remove(f.name)

@pytest.fixture
def result_w_unannotated_csv(request,stat) :
  with tempfile.NamedTemporaryFile('wt',delete=False) as f :
      new_stat = stat.copy()
      new_stat.loc['gene11'] = 0
      new_stat.loc['gene12'] = 0
      new_stat.loc['gene13'] = 0
      print(new_stat)

      df = pandas.DataFrame({
          'negnew_stat':-new_stat.values,
          'nonsense':np.random.random(size=new_stat.size),
          'new_stat':new_stat.values,
          'gene':new_stat.index.tolist()
          },
          index=new_stat.index
      )
      df.to_csv(f.name,index_label='id')

  yield f.name

  # cleanup the csv
  os.remove(f.name)

@r_test
@fgsea_test
def test_fgsea_id_type_mismatch(gmt_obj,stat) :
    from de_toolkit.enrich import fgsea

    # rename the stat index so there are no matches
    stat.index = ['X'+_ for _ in stat.index]
    with pytest.raises(Exception) :
        res = fgsea(gmt_obj,stat,minSize=1)

@r_test
@fgsea_test
def test_fgsea_filter_unannot_cli(gmt_file,result_w_unannotated_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    #TODO I WAS TESTING --filter-unannotated
    with tempfile.NamedTemporaryFile('wt') as f:

        # test multilevel flag
        main([
            'detk-enrich','fgsea','--nperm=100',
            '--filter-unannotated','--minSize=1',
            gmt_file,result_w_unannotated_csv,'-o',f.name
        ])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
        assert all(res.loc[['set4','set5'],'NES'] > 0)
@r_test
@fgsea_test
def test_fgsea(gmt_obj,stat) :
    from de_toolkit.enrich import fgsea
    import numpy

    # this way has set1, set2, and set3 negative NES,
    # set4 and set5 positive
    res = fgsea(gmt_obj,stat,minSize=1)
    assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
    assert all(res.loc[['set4','set5'],'NES'] > 0)

    # same thing with parallelism
    res = fgsea(gmt_obj,stat,minSize=1,nproc=2)
    assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
    assert all(res.loc[['set4','set5'],'NES'] > 0)

    # this is the opposite direction
    res = fgsea(gmt_obj,-stat,minSize=1)
    assert all(res.loc[['set1','set2','set3'],'NES'] > 0)
    assert all(res.loc[['set4','set5'],'NES'] < 0)

    # if the stat column has NAs in it, fgsea warns the user that the
    # gene has been filtered out
    na_stat = stat.copy().astype(float)
    na_stat[0] = np.nan
    with pytest.warns(UserWarning) :
        res = fgsea(gmt_obj,na_stat,minSize=1)

    # if some of the gene names are None detk should handle gracefully
    # and warn user
    null_stat = stat.copy().astype(float)
    null_stat.rename(index={'gene1':None},inplace=True)
    null_stat.rename(index={'gene2':numpy.nan},inplace=True)
    null_stat.rename(index={'gene3':('a','tuple')},inplace=True)
    with pytest.warns(UserWarning) :
        res = fgsea(gmt_obj,null_stat,minSize=1)

@r_test
@fgsea_test
def test_fgsea_multilevel(gmt_obj,stat) :
    from de_toolkit.enrich import fgsea
    import numpy

    # same thing, but with multilevel mode
    res = fgsea(gmt_obj,stat,minSize=1,multilevel=True,nperm=100)
    assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
    assert all(res.loc[['set4','set5'],'NES'] > 0)

@r_test
@fgsea_test
def test_fgsea_cli(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:

        # normal operation, picks stat as last numerical column
        main(['detk-enrich','fgsea','--minSize=1',gmt_file,result_csv,'-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
        assert all(res.loc[['set4','set5'],'NES'] > 0)

@r_test
@fgsea_test
def test_fgsea_cli_cores(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr


    with tempfile.NamedTemporaryFile('wt') as f:

        # normal operation, with two cores
        main(['detk-enrich','fgsea','--cores=2','--minSize=1',gmt_file,result_csv,'-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
        assert all(res.loc[['set4','set5'],'NES'] > 0)

@r_test
@fgsea_test
def test_fgsea_cli_routput(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:
        with tempfile.TemporaryDirectory() as d :
            main(['detk-enrich','fgsea','--routput-dir={}'.format(d),'--minSize=1',gmt_file,result_csv,'-o',f.name])
            res = pandas.read_csv(f.name,index_col=0)
            assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
            assert all(res.loc[['set4','set5'],'NES'] > 0)
            assert os.path.exists(os.path.join(d,'script.R'))

            with open(os.path.join(d,'stdout')) as f :
                out = f.read()
                assert len(out) != 0
@r_test
@fgsea_test
def test_fgsea_cli_alt_statcol(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:

        # different column as statistic
        main(['detk-enrich','fgsea','--minSize=1','--statcol=negstat',gmt_file,
            result_csv,'-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] > 0)
        assert all(res.loc[['set4','set5'],'NES'] < 0)

@r_test
@fgsea_test
def test_fgsea_cli_abs_statcol(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:

        # different column as statistic, but with abs value is
        # the same as normal stat
        main(['detk-enrich','fgsea','--minSize=1','--statcol=negstat','--abs',
            gmt_file,result_csv,'-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
        assert all(res.loc[['set4','set5'],'NES'] > 0)

@r_test
@fgsea_test
def test_fgsea_cli_ascending(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:

        # sort ascending operation on last numerical column
        main(['detk-enrich','fgsea','--minSize=1','-a',gmt_file,result_csv,
            '-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] > 0)
        assert all(res.loc[['set4','set5'],'NES'] < 0)

@r_test
@fgsea_test
def test_fgsea_cli_idcol(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:

        # speficy idcol
        main(['detk-enrich','fgsea','--minSize=1','--idcol=gene',gmt_file,
            result_csv,'-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
        assert all(res.loc[['set4','set5'],'NES'] > 0)

@r_test
@fgsea_test
def test_fgsea_cli_wrapr_cores(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:
        with tempfile.NamedTemporaryFile('rt') as r_f :
            # check that the R script got the cores argument, which I assume
            # means it ran with that number of cores question mark?
            # this also is a test that the rda functionality works
            main(['detk-enrich','fgsea','--minSize=1','--cores=2',
                '--rda={}'.format(r_f.name),gmt_file,result_csv,'-o',f.name])
            res = pandas.read_csv(f.name,index_col=0)
            assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
            assert all(res.loc[['set4','set5'],'NES'] > 0)

            with wrapr('cat(readRDS("{}")$params$nproc)'.format(r_f.name)) as r :
                assert r.stdout == '2'
@r_test
@fgsea_test
def test_fgsea_multilevel_cli(gmt_file,result_csv) :
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile('wt') as f:

        # test multilevel flag
        main(['detk-enrich','fgsea','--nperm=100','--multilevel','--minSize=1',gmt_file,result_csv,'-o',f.name])
        res = pandas.read_csv(f.name,index_col=0)
        assert all(res.loc[['set1','set2','set3'],'NES'] < 0)
        assert all(res.loc[['set4','set5'],'NES'] > 0)


def test_gmt_obj(gset_dict) :
    from de_toolkit.enrich import GMT

    gmt = GMT(gset_dict)
    assert gmt['set1'].name == 'set1'
    assert gmt['set1'].ids == gset_dict['set1']

    gmt['setX'] = gset_dict['set1']

    assert gmt['setX'].name == 'setX'
    assert gmt['setX'].ids == gset_dict['set1']

    gmt.add('setY',gset_dict['set1'])

    assert gmt['setY'].name == 'setY'
    assert gmt['setY'].desc == 'setY'
    assert gmt['setY'].ids == gset_dict['set1']

    gmt.add('setZ',gset_dict['set1'],desc='yippee')

    assert gmt['setZ'].name == 'setZ'
    assert gmt['setZ'].desc == 'yippee'
    assert gmt['setZ'].ids == gset_dict['set1']

def test_gmt_file(gset_dict, gmt_file) :
    from de_toolkit.enrich import GMT

    gmt = GMT()
    gmt.load_file(gmt_file)

    assert gmt['set1'].name == 'set1'
    assert gmt['set1'].ids == gset_dict['set1']

    with tempfile.NamedTemporaryFile('rt') as out_f :
        gmt.write_file(out_f.name)
        with open(out_f.name) as f :
            line = next(f).strip().split('\t')
            assert line[0] == 'set1'
            assert line[1] == 'set1'
            assert line[2:] == ['gene1','gene2','gene3']

def test_gmt_file_w_unicode(gset_dict, gmt_file_w_unicode) :
    from de_toolkit.enrich import GMT

    gmt = GMT()
    gmt.load_file(gmt_file_w_unicode)

    assert gmt['set1'].name == 'set1'
    assert gmt['set1'].desc == 'tgf\u03b1'

