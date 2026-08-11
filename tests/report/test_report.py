import docopt
import gzip
import json
import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest

from de_toolkit.common import DetkModule
from de_toolkit.version import __version__

@pytest.fixture
def fake_module(request) :
    class FakeModule(DetkModule) :
        def __init__(self) :
            self['params'] = {'a':1}
            self['properties'] = {'stuff':'junk'}
    return FakeModule()

def test_report_cli(fake_module):
    from de_toolkit.report import main, DetkReport
    with pytest.raises(docopt.DocoptExit) :
        main()

    main(['report','generate'])
    main(['detk-report','generate'])

    with pytest.raises(docopt.DocoptExit) :
        main(['detk-report','generate','oogabooga'])

    with TemporaryDirectory() as d :
        with DetkReport(d) as r :
            r.add_module(fake_module,'counts.csv','new_counts.csv')
        fn = os.path.join(d,'detk_report.html')
        assert os.path.exists(fn)
        os.remove(fn)
        assert not os.path.exists(fn)
        main(['detk-report','generate',f'--report-dir={d}'])
        assert os.path.exists(fn)

    main(['report','clean'])
    main(['detk-report','clean'])

    with pytest.raises(docopt.DocoptExit) :
        main(['detk-report','clean','oogabooga'])

def test_numpyencoder() :
    from de_toolkit.report import NumpyEncoder
    from functools import partial

    d = partial(json.dumps, cls=NumpyEncoder)

    assert d(1) == '1'
    assert d(1.2039820493842) == '1.204'
    assert d(120398.20493842) == '120398.205'
    assert d([1,1.2039820493842]) == '[1, 1.204]'
    assert d({'a':1,'b':1.2039820493842}) == '{"a": 1, "b": 1.204}'
    assert d({'c':{'a':1,'b':1.2039820493842}}) == '{"c": {"a": 1, "b": 1.204}}'
    assert d([{'a': 1, 'b':[{'c': 1.024}]}]) == '[{"a": 1, "b": [{"c": 1.024}]}]'

def test_detk_module_json(fake_module):
    from de_toolkit.report import DetkModuleJSON, hash_str

    with TemporaryDirectory() as d :
        DetkModuleJSON(fake_module,json_dir=d).write()
        # hashed filename should be
        fn = hash_str('fakemodule{"a": 1}-'+__version__)+'.json'
        print(fn)
        assert os.path.exists(os.path.join(d,fn))

        DetkModuleJSON(
                fake_module,
                json_path=os.path.join(d,'fn.json')
            ).write(indent=2)
        assert os.path.exists(os.path.join(d,'fn.json'))

        with open(os.path.join(d,'fn.json')) as f :
            d = json.load(f)
            assert d['name'] == 'fakemodule'
            assert d['detk_version'] == __version__
            assert d['params'] == {'a': 1}

def test_detk_report(fake_module) :
    from de_toolkit.report import DetkReport

    with TemporaryDirectory() as d :
        with DetkReport(d) as r :
            r.add_module(fake_module,'counts.csv','new_counts.csv')

        assert os.path.exists(os.path.join(d,'detk_report.html'))

def _run_detk(args, cwd):
    '''Run a detk console script as a real subprocess, as a user would.'''
    env = dict(os.environ)
    # make sure the console scripts of the running interpreter's environment
    # win, wherever pytest was launched from
    env['PATH'] = os.path.dirname(sys.executable) + os.pathsep + env.get('PATH', '')
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    assert p.returncode == 0, (
        f'{" ".join(args)} failed with code {p.returncode}\n'
        f'stdout:\n{p.stdout}\nstderr:\n{p.stderr}'
    )


def test_report_generate(tmp_path):
    '''End-to-end: chain detk CLI tools and generate a report, no workflow
    manager involved (this replaced the old Snakemake-driven test).'''
    fixture_dir = os.path.dirname(__file__)

    # stage the count matrices and sample info into a scratch dir
    for gz in ('all_mRNA_nonzero_raw_counts_trim.csv.gz',
               'all_mRNA_nonzero_norm_counts_trim.csv.gz'):
        with gzip.open(os.path.join(fixture_dir, gz), 'rb') as f_in, \
                open(tmp_path / gz[:-3], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    shutil.copy(os.path.join(fixture_dir, 'sample_info.csv'), tmp_path)

    cwd = str(tmp_path)
    for kind in ('raw', 'norm'):
        _run_detk(['detk-stats', 'summary', '--log',
                   f'all_mRNA_nonzero_{kind}_counts_trim.csv',
                   '-o', f'{kind}_summary_stats.csv',
                   '--column-data=sample_info.csv'], cwd)
    _run_detk(['detk-filter', 'mean(all) > 10',
               '-o', 'norm_filtered.csv',
               'all_mRNA_nonzero_norm_counts_trim.csv'], cwd)
    _run_detk(['detk-report', 'generate'], cwd)

    report = tmp_path / 'detk_report' / 'detk_report.html'
    assert report.exists()
    # the emitted module JSON should have accumulated across invocations
    json_files = list((tmp_path / 'detk_report' / 'json').glob('*.json'))
    assert len(json_files) >= 3
    html = report.read_text()
    for module in ('basestats', 'coldist', 'filtercounts'):
        assert module in html
