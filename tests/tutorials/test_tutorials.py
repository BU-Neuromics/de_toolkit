"""Every tutorial page runs as one test (DETK-0064).

The pages are docs/tutorials/*.md (but the index) and any other docs page
carrying a ``<!-- tutorial -->`` marker. Run one with, for example,
``uv run pytest tests/tutorials -k airway``.
"""

import pytest
from tutorial_runner import DOCS, discover


@pytest.mark.parametrize(
    "page", [p.relative_to(DOCS).as_posix() for p in discover()], ids=lambda p: p
)
def test_tutorial(page, tutorial_workdir):
    tutorial_workdir(page)
