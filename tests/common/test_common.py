import docopt
import pytest
from de_toolkit.common import main, InvalidDesignException, DetkModule

def test_cli() :
    with pytest.raises(docopt.DocoptExit) :
        main()

def test_cli_version(monkeypatch) :
        from io import StringIO

        import sys
        stdout = StringIO()
        monkeypatch.setattr(sys,'stdout', stdout)

        main(['detk','--version'])

        from de_toolkit.common import __version__
        assert stdout.getvalue().strip() == __version__

def test_CountMatrix(
    fake_counts_pandas_dataframe
    ,fake_column_data_pandas_dataframe
    ) :

    from de_toolkit import CountMatrix
    from de_toolkit.common import SampleMismatchException

    # with no column data
    mat = CountMatrix(
        fake_counts_pandas_dataframe
    )

    # with column data
    mat = CountMatrix(
        fake_counts_pandas_dataframe
        ,column_data=fake_column_data_pandas_dataframe
    )
    assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
    assert all(mat.feature_names == fake_counts_pandas_dataframe.index)

    # with column data and design
    mat = CountMatrix(
        fake_counts_pandas_dataframe
        ,column_data=fake_column_data_pandas_dataframe
        ,design='cont_cov ~ category[case] + counts'
    )
    print(mat.column_data.columns)
    assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
    assert all(mat.feature_names == fake_counts_pandas_dataframe.index)
    assert mat.design == 'cont_cov ~ Intercept + category__cont + counts'

    # missing a counts column
    with pytest.raises(InvalidDesignException) :
        mat = CountMatrix(
            fake_counts_pandas_dataframe
            ,column_data=fake_column_data_pandas_dataframe
            ,design='cont_cov ~ category[case]'
        )
    

    # set invalid design
    with pytest.raises(InvalidDesignException) :
        mat = CountMatrix(
            fake_counts_pandas_dataframe
            ,column_data=fake_column_data_pandas_dataframe
            ,design='cont_cov ~ category[case] + counts'
        )
        mat.design = 'oogabooga'
     
    # with strict
    mat = CountMatrix(
        fake_counts_pandas_dataframe
        ,column_data=fake_column_data_pandas_dataframe
        ,strict=True
    )
    assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
    assert all(mat.feature_names == fake_counts_pandas_dataframe.index)

    # with violations of strict
    # change the order of count columns wrt column data
    fake_counts_pandas_dataframe.columns = fake_counts_pandas_dataframe.columns[::-1]
    with pytest.raises(SampleMismatchException) :
        mat = CountMatrix(
            fake_counts_pandas_dataframe
            ,column_data=fake_column_data_pandas_dataframe
            ,strict=True
        )

    # add an additional column
    fake_counts_pandas_dataframe['d'] = 0
    with pytest.raises(SampleMismatchException) :
        mat = CountMatrix(
            fake_counts_pandas_dataframe
            ,column_data=fake_column_data_pandas_dataframe
            ,strict=True
        )
    
    # with different sample names and not strict
    mat = CountMatrix(
        fake_counts_pandas_dataframe
        ,column_data=fake_column_data_pandas_dataframe
        ,strict=False
    )
    assert sorted(mat.sample_names) == sorted(fake_column_data_pandas_dataframe.index)

    # bad cov
    with pytest.raises(InvalidDesignException) :
        mat.design = 'category ~ cont_covx + counts'

    # test warning when the design matrix samples get truncated due
    # to missing data
    fake_coldata_with_na = fake_column_data_pandas_dataframe.copy()
    fake_coldata_with_na.loc['a','cont_cov'] = None
    with pytest.warns(UserWarning) :
        mat = CountMatrix(
                fake_counts_pandas_dataframe
                ,fake_coldata_with_na
                ,design='category ~ cont_cov + counts'
        )
        assert (mat.counts.columns == mat.column_data.index).all()
        assert (mat.counts.columns == mat.design_matrix.full_matrix.index).all()
        assert (mat.column_data.index == mat.design_matrix.full_matrix.index).all()

def test_CountMatrixFile(
    fake_counts_csv
    ,fake_column_data_csv
    ) :
    from de_toolkit import CountMatrixFile

    mat = CountMatrixFile(
        fake_counts_csv
        ,column_data_f=fake_column_data_csv
    )

################################################################################
# DetkModule base class
def test_DetkModule() :
        from de_toolkit.common import __version__
        stat = DetkModule()
        assert stat.json == {
                        'name':'detkmodule',
                        'params': {},
                        'properties': {}
                        }
        assert stat.name == 'detkmodule'
        assert stat.params == {}
        assert stat.output == []
        assert stat.properties == {}
