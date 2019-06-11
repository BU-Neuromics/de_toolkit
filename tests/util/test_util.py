import csv
import docopt
import numpy as np
import pandas
import pytest
import sys
from tempfile import NamedTemporaryFile

from de_toolkit.util import main

def is_windows() :
    return sys.platform in ('win32','cygwin')

@pytest.mark.skipif(is_windows(), reason='not sure how to test which() on Windows')
def test_which() :
    from de_toolkit.util import which
    assert which('sh') == '/bin/sh'

@pytest.fixture
def fake_tidy_counts_csv(request) :
    counts_data = [
            ['gene','A','B','C'],
            ['nogene',0,0,0]
    ]
    with pytest.temp_csv_wrap(counts_data,',') as f :
        yield f.name


@pytest.fixture
def fake_untidy_counts_csv(request) :
    counts_data = [
            ['gene','A','B','C','D'],
            ['nogene',0,0,0,0]
    ]
    with pytest.temp_csv_wrap(counts_data,',') as f :
        yield f.name

@pytest.fixture
def fake_tidy_column_data_csv(request) :
    column_data = [
            ['sample','col'],
            ['A',0],
            ['B',0],
            ['C',0]
    ]
    with pytest.temp_csv_wrap(column_data,',') as f :
        yield f.name


@pytest.fixture
def fake_untidy_column_data_csv(request) :
    column_data = [
            ['sample','col'],
            ['A',0],
            ['B',0],
            ['C',0],
            ['E',0]
    ]
    with pytest.temp_csv_wrap(column_data,',') as f :
        yield f.name

def test_util_cli() :
  with pytest.raises(docopt.DocoptExit) :
    main()

def test_tidy_cli(fake_untidy_counts_csv, fake_untidy_column_data_csv) :
    with NamedTemporaryFile() as counts_out :
        with NamedTemporaryFile() as col_out :
            main(['detk-util','tidy',
                '-v',
                '-o',counts_out.name,
                '-p',col_out.name,
                fake_untidy_counts_csv,fake_untidy_column_data_csv
                ]
            )
            with open(counts_out.name) as f :
                print(f.read())
            counts = pandas.read_csv(counts_out.name,index_col=0)
            print(counts)
            col = pandas.read_csv(col_out.name,index_col=0)
            print(col)
            assert all(counts.columns == col.index)

def test_tidy_counts_cli(
        fake_untidy_counts_csv,
        fake_tidy_column_data_csv,
        fake_untidy_column_data_csv) :

    # untidy counts are tidied by tidy column data
    with NamedTemporaryFile() as counts_out :
        main(['detk-util','tidy-counts',
            fake_untidy_counts_csv,fake_tidy_column_data_csv,
            '-o',counts_out.name
            ]
        )
        counts = pandas.read_csv(counts_out.name,index_col=0)
        col = pandas.read_csv(fake_tidy_column_data_csv,index_col=0)
        assert all(counts.columns == col.index)

    # untidy counts are not tidied by untidy column data
    # the untidy column data has an extra row ID not found in the counts
    with pytest.raises(SystemExit) :
        main(['detk-util','tidy-counts',
            fake_untidy_counts_csv,fake_untidy_column_data_csv,
            ]
        )

def test_tidy_covs_cli(
        fake_tidy_counts_csv,
        fake_untidy_counts_csv,
        fake_untidy_column_data_csv) :

    # untidy column data are tidied by tidy counts
    with NamedTemporaryFile() as covs_out :
        main(['detk-util','tidy-covs',
            fake_tidy_counts_csv,fake_untidy_column_data_csv,
            '-o',covs_out.name
            ]
        )
        counts = pandas.read_csv(fake_tidy_counts_csv,index_col=0)
        col = pandas.read_csv(covs_out.name,index_col=0)
        assert all(counts.columns == col.index)

    # untidy column data are not tidied by untidy counts data
    # the untidy column data has an extra row ID not found in the counts
    with pytest.raises(SystemExit) :
        main(['detk-util','tidy-covs',
            fake_untidy_counts_csv,fake_untidy_column_data_csv,
            ]
        )

