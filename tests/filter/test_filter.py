import docopt
import pytest
import pandas
import pytest
from tempfile import NamedTemporaryFile
from de_toolkit.filter import parse_filter_command, main
from de_toolkit.common import CountMatrix


@pytest.fixture
def filter_count_obj(request) :

    nsamp = 20
    hsamp = int(nsamp/2)
    qsamp = int(nsamp/4)

    samp_names = ['id{}'.format(_) for _ in range(nsamp)]
    sample_info = [
            samp_names,
            ['case']*hsamp+['cont']*hsamp
        ]
    sample_info = pandas.DataFrame(
        list(zip(*sample_info)),
        columns=('id','cov'),
        index=samp_names
    )

    # gene00 == 1
    # gene01 == 10
    # gene02 == 100
    # gene03 == 1000
    # gene04 == 10000
    counts = [[10**_]*nsamp for _ in range(5)]

    # gene05 == 10 0s and 10 1000s
    # gene06 == 10 10s and 10 1000s
    # gene07 == 10 100s and 10 1000s
    # gene08 == 5 0s, 5 1s, 5 0s, 5 1s
    # gene09 == 3 0s, 7 1s, 3 0s, 7 1s
    # gene10 == 8 0s, 2 1s, 8 0s, 2 1s
    # gene11 == all zeros
    counts.extend([
        [0]*hsamp+[1000]*hsamp,
        [10]*hsamp+[1000]*hsamp,
        [100]*hsamp+[1000]*hsamp,
        [0]*qsamp+[1]*qsamp+[0]*qsamp+[1]*qsamp,
        [0]*3+[1]*(hsamp-3)+[0]*3+[1]*(hsamp-3),
        [0]*8+[1]*(hsamp-8)+[0]*8+[1]*(hsamp-8),
        [0]*nsamp
    ])
    count_names = ['gene{:02d}'.format(_) for _ in range(len(counts))]
    counts = pandas.DataFrame(
        counts,
        index=count_names,
        columns=samp_names
    )

    return CountMatrix(counts,sample_info)

def test_filter_cli(filter_count_obj):

    with NamedTemporaryFile('wt') as counts_f :
        with NamedTemporaryFile('wt') as cov_f :

            filter_count_obj.counts.to_csv(counts_f)
            counts_f.flush()

            with NamedTemporaryFile('wt') as out_f :
                main(['detk-filter','-o',out_f.name,'mean(all) == 1 or mean(all) == 0',counts_f.name])
                df = pandas.read_csv(out_f.name,index_col=0)
                assert all(df.index == ['gene00','gene11'])

            filter_count_obj.column_data.to_csv(cov_f)
            cov_f.flush()

            with NamedTemporaryFile('wt') as out_f :
                main(['detk','filter','-o',out_f.name,'mean(all) == 1 or mean(all) == 0',counts_f.name,cov_f.name])
                df = pandas.read_csv(out_f.name,index_col=0)
                assert all(df.index == ['gene00','gene11'])

            with NamedTemporaryFile('wt') as out_f :
                main(['detk-filter','-o',out_f.name,'mean(all) == 1 or mean(all) == 0',counts_f.name,cov_f.name])
                df = pandas.read_csv(out_f.name,index_col=0)
                assert all(df.index == ['gene00','gene11'])

            with NamedTemporaryFile('wt') as out_f :
                main(['detk-filter','-o',out_f.name,'nonzero(cov[case]) == 0 and zero(cov[cont]) == 0',counts_f.name,cov_f.name])
                df = pandas.read_csv(out_f.name,index_col=0)
                assert all(df.index == ['gene05'])

def test_parser(filter_count_obj):

    p = parse_filter_command('median(all) < 3')
    assert repr(p) == "Clause('median',ColSpec(field=None,group=None),'<',3.0)"

    with pytest.raises(Exception) :
        parse_filter_command('albkajsl')

    p = parse_filter_command('median(all) < 3')
    assert p(filter_count_obj) == {'gene00','gene08','gene09','gene10','gene11'}

    p = parse_filter_command('median(all) > 3')
    assert p(filter_count_obj) == {'gene01','gene02','gene03','gene04','gene05','gene06','gene07'}

    p = parse_filter_command('mean(all) > 3')
    assert p(filter_count_obj) == {'gene01','gene02','gene03','gene04','gene05','gene06','gene07'}

    p = parse_filter_command('mean(cov) > 3')
    assert p(filter_count_obj) == {'gene01','gene02','gene03','gene04','gene05','gene06','gene07'}

    obj_copy = filter_count_obj.copy()
    obj_copy.column_data = None
    with pytest.raises(Exception) :
        p(obj_copy)

    p = parse_filter_command('mean(cov[case]) > 3')
    assert p(filter_count_obj) == {'gene01','gene02','gene03','gene04','gene06','gene07'}

    p1 = parse_filter_command('median(all) > 3')
    p2 = parse_filter_command('mean(cov[case]) > 3 or mean(cov[cont]) > 3')
    assert p1(filter_count_obj) == p2(filter_count_obj)

    p1 = parse_filter_command('mean(cov[case]) > 3')
    p2 = parse_filter_command('mean(cov[case]) > 3 and mean(cov[cont]) > 3')
    assert p1(filter_count_obj) == p2(filter_count_obj)

    p = parse_filter_command('nonzero(all) >= 20')
    assert p(filter_count_obj) == {'gene00','gene01','gene02','gene03','gene04','gene06','gene07'}

    p = parse_filter_command('nonzero(all) >= 0.5')
    assert p(filter_count_obj) == {'gene00','gene01','gene02','gene03','gene04','gene05','gene06','gene07','gene08','gene09'}

    p = parse_filter_command('nonzero(all) >= 0.8')
    assert p(filter_count_obj) == {'gene00','gene01','gene02','gene03','gene04','gene06','gene07'}
    
    p = parse_filter_command('nonzero(cov[case]) == 0')
    assert p(filter_count_obj) == {'gene05','gene11'}

    p = parse_filter_command('nonzero(cov[case]) == 0 and zero(cov[cont]) == 0')
    assert p(filter_count_obj) == {'gene05'}

    # misspecified group value
    with pytest.warns(UserWarning) :
        p = parse_filter_command('nonzero(cov[cse]) == 0')
        p(filter_count_obj)

    p = parse_filter_command('(mean(cov[case]) >= 100 and mean(cov[cont]) >= 1000) or nonzero(all) == 0')
    assert p(filter_count_obj) == {'gene03','gene04','gene07','gene11'}

    p = parse_filter_command('nonzero(all) == -1')
    assert p(filter_count_obj) == set()
