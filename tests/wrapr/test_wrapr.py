import docopt
import pytest
from de_toolkit import wrapr
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

# decorator for skipping if Rscript is not installed
r_test = pytest.mark.skipif(
    not wrapr.check_r(), reason="Rscript executable not found, skipping test"
)


@r_test
def test_wrapr_cli_check(monkeypatch):

    # check default run mode
    with NamedTemporaryFile("wt") as f:
        f.write("library(base)")
        wrapr.main(["detk-wrapr", "run", f.name])

    # check run mode with specified routput dir
    with NamedTemporaryFile("wt") as f:
        with TemporaryDirectory() as d:
            f.write("library(base)")
            wrapr.main(["detk-wrapr", "run", f"--routput-dir={d}", f.name])
            assert os.path.exists(os.path.join(d, "script.R"))

    with pytest.raises(docopt.DocoptExit):
        wrapr.main()

    monkeypatch.setattr(wrapr, "check_r", lambda: False)
    monkeypatch.setattr(wrapr, "check_r_package", lambda x: True)
    with pytest.raises(SystemExit):
        wrapr.main(["detk-wrapr", "check"])

    monkeypatch.setattr(wrapr, "check_r", lambda: True)
    monkeypatch.setattr(wrapr, "check_r_package", lambda x: False)
    with pytest.raises(SystemExit):
        wrapr.main(["detk-wrapr", "check"])


def test_get_r_path(monkeypatch):
    from de_toolkit import wrapr

    # when false
    def f(*args, **kwargs):
        return "/usr/bin/Rscript"

    monkeypatch.setattr(wrapr, "which", f)
    assert wrapr.get_r_path() == "/usr/bin/Rscript"


@r_test
def test_check_r(monkeypatch):
    from de_toolkit import wrapr

    # when false
    def f(*args, **kwargs):
        return None

    monkeypatch.setattr(wrapr, "get_r_path", f)
    assert not wrapr.check_r()

    # when true
    def f(*args, **kwargs):
        return "/usr/bin/Rscript"

    monkeypatch.setattr(wrapr, "get_r_path", f)
    assert wrapr.check_r()


@r_test
def test_require_r(monkeypatch):
    from de_toolkit import wrapr

    # these tests only run if R is already installed
    # when true
    wrapr.require_r(lambda x: x)(None)

    # test a nonsense package
    with pytest.raises(wrapr.RPackageMissing):
        wrapr.require_r("arglebargle")(lambda x: x)(None)

    def f2(*args, **kwargs):
        return False

    monkeypatch.setattr(wrapr, "check_r_package", f2)
    with pytest.raises(wrapr.RPackageMissing):
        wrapr.require_r(lambda x: x)(None)

    # when fail
    def f(*args, **kwargs):
        return None

    monkeypatch.setattr(wrapr, "get_r_path", f)
    with pytest.raises(wrapr.RscriptExecutableNotFound):
        wrapr.require_r(lambda x: x)(None)


@r_test
def test_require_deseq2(monkeypatch):
    from de_toolkit import wrapr

    # when fail
    def f(*args, **kwargs):
        return False

    monkeypatch.setattr(wrapr, "check_deseq2", f)
    with pytest.raises(wrapr.RPackageMissing):
        wrapr.require_deseq2(lambda x: x)(None)

    # when true
    def f(*args, **kwargs):
        return True

    monkeypatch.setattr(wrapr, "check_deseq2", f)
    wrapr.require_deseq2(lambda x: x)(None)


@r_test
def test_WrapR(fake_counts_obj):
    from de_toolkit import wrapr
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile("wt") as f:
        f.write("cat(length(args))")
        f.flush()
        with wrapr.WrapR(f.name, fake_counts_obj.counts, fake_counts_obj.column_data) as wr:
            wr.execute()
            assert wr.stdout.strip() == "6"
            assert wr.output is None
            assert wr.metadata_out is None
            assert wr.params_out is None


@r_test
def test_wrapr(fake_counts_obj):
    from de_toolkit import wrapr
    import os

    script = "library(base)"
    with wrapr.wrapr(script) as wr:
        assert wr.success

    script = "cat(length(args))"
    with wrapr.wrapr(script, counts=fake_counts_obj.counts) as wr:
        assert wr.stdout.strip() == "6"
        assert wr.output is None
        assert wr.metadata_out is None
        assert wr.params_out is None

    script = """
    write.csv(read.csv(counts.fn),out.fn,row.names=FALSE)
    write.csv(read.csv(metadata.fn),metadata.out.fn,row.names=FALSE)
    """
    with wrapr.wrapr(
        script, counts=fake_counts_obj.counts, metadata=fake_counts_obj.column_data
    ) as wr:
        assert wr.stdout.strip() == ""
        assert wr.output is not None
        assert (wr.output == fake_counts_obj.counts).all().all()
        assert (wr.metadata_out == fake_counts_obj.column_data).all().all()

    with wrapr.wrapr("cat(params$x+3)", params={"x": 3}) as wr:
        assert wr.stdout.strip() == "6"

    with wrapr.wrapr("str(params$x)", params={"x": [1.2, 3.4]}) as wr:
        assert wr.stdout.strip() == "num [1:2] 1.2 3.4"

    with wrapr.wrapr("write_json(list(y=5),params.out.fn)") as wr:
        assert wr.params_out["y"] == 5

    # check for custom r output dir
    with TemporaryDirectory() as d:
        with wrapr.wrapr("library(base)", routput_dir=d) as wr:
            assert wr.success
        assert os.path.exists(os.path.join(d, "script.R"))
        assert os.path.exists(os.path.join(d, "counts.csv"))
        assert os.path.exists(os.path.join(d, "counts_out.csv"))
        assert os.path.exists(os.path.join(d, "meta_in.csv"))
        assert os.path.exists(os.path.join(d, "meta_out.csv"))
        assert os.path.exists(os.path.join(d, "stdout"))
        assert os.path.exists(os.path.join(d, "stderr"))


@r_test
def test_wrapr_fail():
    from de_toolkit import wrapr

    with pytest.raises(wrapr.RExecutionError):
        with wrapr.wrapr("thisisanerror") as wr:
            assert wr.success

    with wrapr.wrapr("thisisanerror", raise_on_error=False) as wr:
        assert not wr.success


@r_test
def test_wrapr_keeps_ids_as_written():
    # read.id.csv reads the first column as text and types the rest as
    # read.csv does, and wrapr reads R's output with its first column as
    # text: 007, 010, 1.10 and 1.1 come back as written (DETK-0015, #67)
    import pandas

    ids = ["007", "010", "1.10", "1.1"]
    samples = ["001", "002"]
    counts = pandas.DataFrame(
        [[1, 2], [3, 4], [5, 6], [7, 8]], index=pandas.Index(ids, name="gene"), columns=samples
    )
    meta = pandas.DataFrame(
        {"x": [0.5, 1.5], "y": ["a", "b"]}, index=pandas.Index(samples, name="sample")
    )
    script = """
    cnts <- read.id.csv(counts.fn, row.names=TRUE)
    stopifnot(identical(rownames(cnts), c("007", "010", "1.10", "1.1")))
    stopifnot(is.numeric(cnts[["001"]]))
    meta <- read.id.csv(metadata.fn, row.names=TRUE)
    stopifnot(identical(rownames(meta), colnames(cnts)))
    stopifnot(is.numeric(meta$x), is.character(meta$y))
    write.csv(cnts, out.fn)
    write.csv(meta, metadata.out.fn)
    """
    with wrapr.wrapr(script, counts=counts, metadata=meta, raise_on_error=True) as wr:
        assert wr.output.index.tolist() == ids
        assert wr.output.columns.tolist() == samples
        assert (wr.output.to_numpy() == counts.to_numpy()).all()
        assert wr.metadata_out.index.tolist() == samples
