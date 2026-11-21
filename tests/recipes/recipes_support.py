"""Shared by the recipe tests: the tutorial runner on the path, and require()."""

import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tutorials"))

from tutorial_runner import (  # noqa: E402
    REQUIRE_ALL_ENV,
    TutorialFailure,
    TutorialSkip,
    run_page,
)

__all__ = ["REQUIRE_ALL_ENV", "TutorialFailure", "TutorialSkip", "run_page", "require"]


def require(program):
    """Skip, with the reason, when *program* is not on PATH; fail instead
    where the CI job that must run everything sets the tutorials' variable."""
    if shutil.which(program) is None:
        reason = f"{program} is not on PATH"
        if os.environ.get(REQUIRE_ALL_ENV, "") not in ("", "0"):
            pytest.fail(f"{reason} (and {REQUIRE_ALL_ENV} is set)", pytrace=False)
        pytest.skip(reason)
