"""Fixtures for the recipe pages under docs/recipes/ (DETK-0062).

A recipe page is a tutorial page (DETK-0064): tests/tutorials runs it as one
test. The checks here are the deeper ones, run on the page's working
directory after its last block, and the failure cases, run on the page's own
recipe commands.
"""

from pathlib import Path

import pytest
from recipes_support import TutorialFailure, TutorialSkip, run_page


@pytest.fixture(scope="session")
def page_workdir(tmp_path_factory):
    """``page_workdir(path)`` runs a docs page once per session and returns its
    working directory; skips or fails as the page does."""
    done = {}

    def get(path):
        path = Path(path)
        if path not in done:
            workdir = tmp_path_factory.mktemp(path.stem, numbered=True)
            try:
                run_page(path, workdir)
                done[path] = (workdir, None)
            except (TutorialSkip, TutorialFailure) as e:
                done[path] = (workdir, e)
        workdir, error = done[path]
        if isinstance(error, TutorialSkip):
            pytest.skip(str(error))
        if error is not None:
            pytest.fail(f"the page did not run:\n{error}", pytrace=False)
        return workdir

    return get
