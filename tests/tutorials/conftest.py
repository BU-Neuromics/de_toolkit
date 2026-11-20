"""Fixtures for the tutorial pages (DETK-0064); see docs/dev/tutorials.md."""

from pathlib import Path

import pytest
from tutorial_runner import DOCS, TutorialFailure, TutorialSkip, run_page


class _Runs:
    """Runs each page once per session and remembers how it went, so the
    page's test and its optional test_<page>.py share one run."""

    def __init__(self, factory):
        self._factory = factory
        self._done = {}

    def __call__(self, page):
        path = Path(page)
        if not path.is_absolute():
            path = DOCS / path
        path = path.resolve()
        if path not in self._done:
            workdir = self._factory.mktemp(path.stem, numbered=True)
            try:
                run_page(path, workdir)
                self._done[path] = (workdir, None)
            except (TutorialSkip, TutorialFailure) as e:
                self._done[path] = (workdir, e)
        return self._done[path]


@pytest.fixture(scope="session")
def tutorial_runs(tmp_path_factory):
    return _Runs(tmp_path_factory)


@pytest.fixture(scope="session")
def tutorial_workdir(tutorial_runs):
    """``tutorial_workdir("tutorials/airway.md")`` runs the page (once per
    session), and returns its working directory after the last block, for
    checks too deep to show on the page. Skips or fails as the page did."""

    def get(page):
        workdir, error = tutorial_runs(page)
        if isinstance(error, TutorialSkip):
            pytest.skip(str(error))
        if error is not None:
            pytest.fail(f"the page did not run:\n{error}", pytrace=False)
        return workdir

    return get
