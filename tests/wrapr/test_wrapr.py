import pytest
from de_toolkit import wrapr

# decorator for skipping if Rscript is not installed
r_test = pytest.mark.skipif(not wrapr.check_r(),reason='Rscript executable not found, skipping test')

def test_get_r_path(monkeypatch) :
    from de_toolkit import util, wrapr
    # when false
    def f(*args,**kwargs):
        return '/usr/bin/Rscript'
    monkeypatch.setattr(util,'which',f)
    assert wrapr.get_r_path() == '/usr/bin/Rscript'

@r_test
def test_check_r(monkeypatch) :
    from de_toolkit import wrapr

    # when false
    def f(*args,**kwargs):
        return None
    monkeypatch.setattr(wrapr,'get_r_path',f)
    assert wrapr.check_r() == False

    # when true
    def f(*args,**kwargs):
        return '/usr/bin/Rscript'
    monkeypatch.setattr(wrapr,'get_r_path',f)
    assert wrapr.check_r() == True

@r_test
def test_require_r(monkeypatch) :
    from de_toolkit import wrapr

    # when fail
    def f(*args,**kwargs):
        return None
    monkeypatch.setattr(wrapr,'get_r_path',f)
    with pytest.raises(wrapr.RscriptExecutableNotFound) :
        wrapr.require_r(lambda x: x)(None)

    # when true
    def f(*args,**kwargs):
        return '/usr/bin/Rscript'
    monkeypatch.setattr(wrapr,'get_r_path',f)
    wrapr.require_r(lambda x: x)(None)

    def f2(*args,**kwargs):
        return False
    monkeypatch.setattr(wrapr,'get_r_path',f)
    monkeypatch.setattr(wrapr,'check_jsonlite',f2)
    with pytest.raises(wrapr.RPackageMissing) :
        wrapr.require_r(lambda x: x)(None)

@r_test
def test_WrapR(fake_counts_obj):
    from de_toolkit import wrapr
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile('wt') as f :
        f.write('cat(length(args))')
        f.flush()
        with wrapr.WrapR(f.name,
                         fake_counts_obj.counts,
                         fake_counts_obj.column_data
                        ) as wr :
            wr.execute()
            assert wr.stdout.strip() == '6'
            assert wr.counts_out is None
            assert wr.metadata_out is None
            assert wr.params_out is None

@r_test
def test_wrapr(fake_counts_obj):
    from de_toolkit import wrapr

    script = 'library(base)'
    with wrapr.wrapr(script) as wr :
        assert wr.success

    script = 'cat(length(args))'
    with wrapr.wrapr(script,fake_counts_obj) as wr :
        assert wr.stdout.strip() == '6'
        assert wr.counts_out is None
        assert wr.metadata_out is None
        assert wr.params_out is None

    script = '''
    write.csv(read.csv(counts.fn),counts.out.fn,row.names=FALSE)
    write.csv(read.csv(metadata.fn),metadata.out.fn,row.names=FALSE)
    '''
    with wrapr.wrapr(script,fake_counts_obj) as wr :
        assert wr.stdout.strip() == ''
        assert wr.counts_out is not None
        assert (wr.counts_out == fake_counts_obj.counts).all().all()
        assert (wr.metadata_out == fake_counts_obj.column_data).all().all()

    with wrapr.wrapr('cat(params$x+3)',params={'x':3}) as wr :
        assert wr.stdout.strip() == '6'

    with wrapr.wrapr('str(params$x)',params={'x':[1.2,3.4]}) as wr :
        assert wr.stdout.strip() == 'num [1:2] 1.2 3.4'

    with wrapr.wrapr('write_json(list(y=5),params.out.fn)') as wr :
        assert wr.params_out['y'] == 5

#@r_test
#def test_require_deseq2(monkeypatch) :
#    from de_toolkit import wrapr
#    def f(*args,**kwargs):
#        raise(RRuntimeError('mock'))
#    monkeypatch.setattr(,'importr',f)
#
#    with pytest.raises(RPackageMissingError) :
#        require_deseq2(lambda x: x)
