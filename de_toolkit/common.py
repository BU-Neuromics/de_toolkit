'''
Usage:
    detk norm [options] <args>...
    detk de [options] <args>...
    detk transform [options] <args>...
    detk filter [options] <args>...
    detk stats [options] <args>...
    detk outlier [options] <args>...
    detk wrapr [options] <args>...
'''
from copy import deepcopy
from docopt import docopt
import pandas
import re
import sys
from .patsy_lite import DesignMatrix, PatsyLiteParseError

class InvalidDesignException(Exception): pass
class SampleMismatchException(Exception): pass

class CountMatrix(object) :
    def __init__(self
            ,counts
            ,column_data=None
            ,design=None
            ,strict=False
         ) :

        if column_data is not None :
            # line up the sample names from the column_data and counts matrices
            if strict and (
                len(column_data.index) != len(counts.columns) or
                not all(column_data.index == counts.columns)
            ) :
                raise SampleMismatchException('When *strict* is supplied, the columns '
                    'of the counts file must correspond exactly to the row names in the '
                    'column_data matrix')
            else :
                common_names = counts.columns.intersection(column_data.index)

                # fix to "no memory available" bitbucket issue #4 when matrices are
                # empty
                if len(common_names) < 2 :
                    raise SampleMismatchException('No sample names were found to be in '
                        'common between the counts and column data or specified sample '
                        'names. Check that the first column of the column_data matrix '
                        'and the first row of the counts matrix contain at least 2 values '
                        'in common')

                counts = counts[common_names]
                column_data = column_data.loc[common_names]

        # if the design is provided, it must have a 'counts' term somewhere
        if design is not None and 'counts' not in design :
            raise InvalidDesignException('The term "counts" must exist on at least one '
                'side of the CountsMatrix design')

        # set the things
        self.counts = counts
        self.column_data = column_data

        # set the design no matta wat
        self._design_matrix = None
        self.design = self._original_design = design

        #TODO this is not yet implemented or thought out
        # members to keep track of count mutations
        self.transformed = {}
        self.normalized = {}

    @property
    def column_data(self) :
        return self._column_data

    @column_data.setter
    def column_data(self,column_data) :
        # if column_data does not have a counts column, add one with trivial values
        # so things work
        if column_data is not None and 'counts' not in column_data :
            column_data['counts'] = 0

        self._column_data = column_data

        # update the design matrix by setting the design to itself
        self.design = self.design

    @property
    def design(self) :
        if hasattr(self,'design_matrix') and self.design_matrix is not None :
            return self.design_matrix.design
        if hasattr(self,'_design') :
            return self._design
        return None

    @design.setter
    def design(self,design) :
        self._design = design
        if design is not None and self.column_data is not None :
            try :
                self.design_matrix = DesignMatrix(design,self.column_data)
            except PatsyLiteParseError as e :
                raise InvalidDesignException('Invalid design, patsy lite could not parse '
                    '{}'.format(e.args))
        elif design is not None and self.column_data is None :
            raise InvalidDesignException('There must be column data associated with a '
            'CountMatrix object before specifying a design')

    @property
    def design_matrix(self) :
        return self._design_matrix

    @design_matrix.setter
    def design_matrix(self,design_matrix) :
        self._design_matrix = design_matrix

    @property
    def sample_names(self) :
        return self.counts.columns

    @sample_names.setter
    def sample_names(self,value):
        try :
            self.counts = self.counts[value]
        except Exception as e :
            raise Exception('Sample names provided that are not contained in the '
                'counts matrix')

    @property
    def feature_names(self) :
        return self.counts.index

    @feature_names.setter
    def feature_names(self,value):
        try :
            self.counts = self.counts.loc[value]
        except Exception as e :
            raise Exception('Feaure names provided that are not contained in the '
                'counts matrix')

    def copy(self) :
        return deepcopy(self)

    def transform(self,transf) :
        self.transformed[transf.__name__] = transf(self)

    def add_normalized(self,method='deseq2') :
        pass

class CountMatrixFile(CountMatrix) :

    def __init__(self
        ,count_f
        ,column_data_f=None
        ,design=None
        ,**kwargs
     ) :

        counts = pandas.read_csv(
            count_f
            ,sep=None # sniff the format automatically
            ,engine='python'
            ,index_col=0
        )

        column_data = None
        if column_data_f is not None :
            column_data = pandas.read_csv(
                column_data_f
                ,sep=None
                ,engine='python'
                ,index_col=0
            )

        CountMatrix.__init__(self
            ,counts
            ,column_data=column_data
            ,design=design
            ,**kwargs
        )

def main(argv=sys.argv) :

    cmds = 'norm','de','transform','filter','stats','outlier','wrapr','help'

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmds) :
        docopt(__doc__)
    cmd = argv[1]

    # the individual main methods expect an executable of the form
    # detk-<mode>, but here the detk and mode come as separate arguments
    # concatenate them together and pass them on
    cli_args = ['-'.join(argv[:2])]+argv[2:]

    if cmd == 'norm' :
        from .norm import main
        main(cli_args)
    elif cmd == 'de' :
        from .de import main
        main(cli_args)
    elif cmd == 'transform' :
        from .transform import main
        main(cli_args)
    elif cmd == 'filter' :
        from .filter import main
        main(cli_args)
    elif cmd == 'stats' :
        from .stats import main
        main(cli_args)
    elif cmd == 'outlier' :
        from .outlier import main
        main(cli_args)
    elif cmd == 'wrapr' :
        from .wrapr import main
        main(cli_args)
    elif cmd == 'help' :
        docopt(__doc__,['-h'])


if __name__ == '__main__' :
    main()
