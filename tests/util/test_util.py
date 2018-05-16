import csv
import numpy as np
import pandas
import pytest
import sys
import tempfile

def is_windows() :
    return sys.platform in ('win32','cygwin')

@pytest.mark.skipif(is_windows(), reason='not sure how to test which() on Windows')
def test_which() :
    from .util import which
    assert which('sh') == '/bin/sh'
