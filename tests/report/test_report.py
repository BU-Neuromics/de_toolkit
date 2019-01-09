import docopt
import json
import os
import pytest
import subprocess
from tempfile import TemporaryDirectory

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
        main(['detk-report','generate','--report-dir={}'.format(d)])
        assert os.path.exists(fn)

    main(['report','clean'])
    main(['detk-report','clean'])

    with pytest.raises(docopt.DocoptExit) :
        main(['detk-report','clean','oogabooga'])

def test_detk_module_json(fake_module):
    from de_toolkit.report import DetkModuleJSON, hash_str

    with TemporaryDirectory() as d :
        j = DetkModuleJSON(fake_module,json_dir=d).write()
        # hashed filename should be
        fn = hash_str('fakemodule{"a": 1}-'+__version__)+'.json'
        assert os.path.exists(os.path.join(d,fn))

        j = DetkModuleJSON(
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
    from pprint import pprint

    with TemporaryDirectory() as d :
        with DetkReport(d) as r :
            r.add_module(fake_module,'counts.csv','new_counts.csv')

        assert os.path.exists(os.path.join(d,'detk_report.html'))

# decorator for skipping if snakemake is not installed
def check_snakemake() :
    p = subprocess.run("snakemake -v",shell=True)
    return p.returncode == 0

snakemake_test = pytest.mark.skipif(not check_snakemake(),reason='snakemake executable not found, skipping test')
@snakemake_test
def test_report_generate():
    p = subprocess.run("snakemake --forceall",
            shell=True,
            cwd=os.path.dirname(__file__)
    )
    assert p.returncode == 0
