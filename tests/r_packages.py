"""Skip a test when R, or an R package it needs, is missing.

A test that runs R calls ``skip_without_r("DESeq2")`` (or is marked with
``needs_r("DESeq2")``). With no Rscript on PATH it skips saying so; with
Rscript but without one of the packages it skips naming the first one
missing, so a partial R library gives skips rather than failures.

The check is ``wrapr.check_r_package``, the one detk itself uses before
it runs R, cached per Rscript path and package because the
parametrized tests ask the same question many times.
"""

from functools import cache

import pytest

from de_toolkit import wrapr


@cache
def _has_package(r_path, pkg):
    # r_path is part of the key so that a test pointing PATH at another
    # Rscript (the stub in tests/wrapr/test_r_packages.py) gets its own answer
    return wrapr.check_r_package(pkg)


def missing_r(*packages):
    """What is missing to run R with *packages*: a reason to skip, or None.

    ``"Rscript is not on PATH"`` without R, otherwise
    ``"R package <pkg> is not installed"`` for the first missing package.
    """
    r_path = wrapr.get_r_path()
    if r_path is None:
        return "Rscript is not on PATH"
    for pkg in packages:
        if not _has_package(r_path, pkg):
            return f"R package {pkg} is not installed"
    return None


def skip_without_r(*packages):
    "Skip the calling test unless Rscript and every one of *packages* are present."
    reason = missing_r(*packages)
    if reason:
        pytest.skip(reason)


def needs_r(*packages):
    "A marker that skips the test unless Rscript and every one of *packages* are present."
    reason = missing_r(*packages)
    return pytest.mark.skipif(reason is not None, reason=reason or "")
