"""
tests/r_packages.py, the helper the R tests skip with: a stub Rscript
stands in for an R library that has some packages and lacks others, so
these tests need no R.
"""

import os
import stat

import pytest

import r_packages
from r_packages import missing_r, needs_r, skip_without_r

# a stub Rscript: `Rscript -e "library(pkg)"` succeeds for the packages
# listed here and fails for any other, as R does for a missing package
STUB = """#!/bin/sh
case "$2" in
  "library(fgsea)"|"library(jsonlite)") exit 0 ;;
  *) echo "Error in library($2) : there is no package" >&2; exit 1 ;;
esac
"""


@pytest.fixture
def stub_r(tmp_path, monkeypatch):
    "PATH holds only the stub Rscript, whose library has fgsea and jsonlite"
    if os.name != "posix":
        pytest.skip("the stub Rscript is a shell script")
    rscript = tmp_path / "Rscript"
    rscript.write_text(STUB)
    rscript.chmod(rscript.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path))
    return rscript


@pytest.fixture
def no_r(tmp_path, monkeypatch):
    "PATH has no Rscript"
    monkeypatch.setenv("PATH", str(tmp_path))


def test_nothing_missing_with_the_packages_present(stub_r):
    assert missing_r() is None
    assert missing_r("fgsea", "jsonlite") is None


@pytest.mark.parametrize(
    "packages,named",
    [
        (("DESeq2",), "DESeq2"),
        (("logistf",), "logistf"),
        (("fgsea", "DESeq2", "logistf"), "DESeq2"),
    ],
)
def test_names_the_first_missing_package(stub_r, packages, named):
    assert missing_r(*packages) == f"R package {named} is not installed"


def test_says_rscript_is_missing_without_r(no_r):
    assert missing_r() == "Rscript is not on PATH"
    assert missing_r("fgsea") == "Rscript is not on PATH"


def test_skip_without_r_skips_naming_the_package(stub_r):
    with pytest.raises(pytest.skip.Exception, match="R package DESeq2 is not installed"):
        skip_without_r("fgsea", "DESeq2")
    skip_without_r("fgsea")  # present: no skip


def test_needs_r_marks_a_skip_naming_the_package(stub_r):
    mark = needs_r("logistf")
    assert mark.args == (True,)
    assert mark.kwargs["reason"] == "R package logistf is not installed"
    mark = needs_r("jsonlite")
    assert mark.args == (False,)


def test_the_answer_is_kept_per_rscript(stub_r, tmp_path, monkeypatch):
    # another Rscript on PATH is asked again, not answered from the cache
    assert missing_r("fgsea") is None
    other = tmp_path / "other"
    other.mkdir()
    (other / "Rscript").write_text("#!/bin/sh\nexit 1\n")
    (other / "Rscript").chmod(0o755)
    monkeypatch.setenv("PATH", str(other))
    assert missing_r("fgsea") == "R package fgsea is not installed"
    assert r_packages._has_package(str(stub_r), "fgsea") is True
