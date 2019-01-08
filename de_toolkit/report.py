r'''\
Usage:
    detk-report generate [options]
    detk-report clean [options]
'''

cmd_opts = {
        'generate':r'''\
Usage:
    detk-report generate [options]

Options:
    --dev  Format html for development (larger file size)
''',
        'clean':r'''\
Usage:
    detk-report clean [options]
'''
}

from collections import OrderedDict
from docopt import docopt
from glob import glob
import hashlib
import jinja2
import json
import numpy as np
import os
import pathlib
import pkg_resources
import shutil
import sys
import time
import de_toolkit

# for some reason, pkg_resources can't find assets in de_toolkit
# unless I access __path__???!?
de_toolkit.__path__

from .common import _cli_doc
from .version import __version__

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16,np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, 
            np.float64)):
            return float(obj)
        elif isinstance(obj,(np.ndarray,)): #### This is the fix
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def hash_str(st) :
    return hashlib.md5(st.encode()).hexdigest()

class DetkModuleJSON(object):
    def __init__(self,
            module,
            in_file_path=None,
            out_file_path=None,
            column_data_path=None,
            workdir=None,
            json_dir='.',
            json_path=None) :

        # the json filename is calculated as the combination of
        # the module name, the parameters passed, and the input filename
        repl_file_path = '-' if in_file_path is None else in_file_path

        # since the parameters is a dictionary, convert to a json string
        # to calculate the hash
        param_str = json.dumps(module.params, sort_keys=True, cls=NumpyEncoder)

        module_id = hash_str(module.name+param_str+repl_file_path+__version__)

        filename = '{}.json'.format(module_id)

        if json_path is not None :
            self.filepath = json_path
        else :
            self.filepath = os.path.realpath(os.path.join(json_dir,filename))

        if workdir is None :
            workdir = os.getcwd()

        module_json = module.json
        self.out_d = OrderedDict([
            ('name',module.name),
            ('id',module_id),
            ('detk_version',__version__),
            ('last_modified',int(1000*time.time())),
            ('in_file_path',in_file_path),
            ('out_file_path',out_file_path),
            ('column_data_path',column_data_path),
            ('workdir',workdir),
            ('params',module_json['params']),
            ('properties',module_json['properties'])
        ])

    def write(self,indent=None) :
        '''
        Write out the module JSON to file.

        Each JSON file has one top level object with the following properties:
        - ``name``: name of the module
        - ``id``: machine readable ID
        - ``detk_version``: version of detk that generated this file
        - ``last_modified``: local system timestamp in milliseconds when this
          file was created/modified
        - ``workdir``: path to the directory where detk was run
        - ``in_file_path``: path to the file that was processed
        - ``out_file_path``: path to the file that was output, if available
        - ``column_data_path``: path to the column data file used, if available
        '''

        with open(self.filepath,'wt') as f :
            json.dump(self.out_d,f,indent=indent,cls=NumpyEncoder)

def walk(path) :
    l = []
    for tmpl_path in pkg_resources.resource_listdir('de_toolkit',path) :
        tmpl_path = os.path.join(path,tmpl_path)
        if pkg_resources.resource_isdir('de_toolkit',tmpl_path) :
            l.extend(walk(tmpl_path))
        else :
            l.append(tmpl_path)
    return l

class DetkReport(object):
    def __init__(self, report_dir='./detk_report') :
        self.report_dir = os.path.realpath(report_dir)
        self.json_dir = os.path.join(self.report_dir,'json')
        pathlib.Path(self.json_dir).mkdir(parents=True, exist_ok=True)
        self.report_path = os.path.join(self.report_dir,'detk_report.html')

        self.modules = []

        self._template_data = {
                'data':None,
                'common': {},
                'templates': {},
                'assets': {}
                }

    def add_module(self,
            module,
            in_file_path=None,
            out_file_path=None,
            column_data_path=None,
            workdir=None
            ) :
        'Add and serialize the given module to the report directory'
        module_json = DetkModuleJSON(
                module,
                in_file_path=in_file_path,
                out_file_path=out_file_path,
                column_data_path=column_data_path,
                workdir=workdir,
                json_dir=self.json_dir
        )
        self.modules.append(module_json)

    @property
    def template_name(self) :
        return 'base.html'

    @property
    def template_data(self) :

        template_data = self._template_data

        json_str = self.json

        # loading the whole json object on a single long line is hard on text
        # editors
        template_data['data'] = json.dumps(json_str)

        # format the report
        # do a scan through the json directory to pick up all the existing
        # reports
        module_names = set()
        for module in json_str :
            module_names.add(module.get('name'))

        # load the module templates for the modules found in the report dir
        for asset in ('js','css','html') :
            # common (common) assets
            common_path = 'templates/{}/common.{}'.format(asset,asset)
            if pkg_resources.resource_exists('de_toolkit',common_path) :
                template_data['common'][asset] = \
                    pkg_resources.resource_string('de_toolkit',common_path).decode()

            # module templates
            d = template_data['templates'][asset] = {}
            for name in module_names :
                tmpl_path = 'templates/{}/{}.{}'.format(asset,name,asset)
                if pkg_resources.resource_exists('de_toolkit',tmpl_path) :
                    template_data['templates'][asset][name] = \
                        pkg_resources.resource_string('de_toolkit',tmpl_path).decode()

            # third party assets
            template_data['assets'][asset] = {}
            asset_dir = 'templates/{}/assets/'.format(asset)
            if pkg_resources.resource_exists('de_toolkit',asset_dir) :
                for tmpl_path in walk(asset_dir) :
                    template_data['assets'][asset][tmpl_path] =  \
                        pkg_resources.resource_string('de_toolkit', tmpl_path).decode()

        return template_data

    @property
    def json(self) :

        # write all the module JSON
        for module in self.modules :
            module.write()

        # format the report
        # do a scan through the json directory to pick up all the existing
        # reports
        json_str = []
        for fn in glob(os.path.join(self.json_dir,'*.json')) :
            with open(fn) as f :
                j = f.read().strip()
                json_str.append(json.loads(j))

        return json_str

    def write(self) :

        # write all the module JSON for this report
        for module in self.modules :
            module.write()

        # create and render the template
        template = jinja2.Template(
            pkg_resources.resource_string(
                'de_toolkit','templates/html/{}'.format(
                    self.template_name
                )
            ).decode()
        )

        with open(self.report_path,'w') as f :
            f.write(template.render(**self.template_data))

    def __enter__(self) :
        return self
    def __exit__(self,type,value,traceback):
        self.write()

class DetkReportDev(DetkReport) :
    @property
    def template_name(self) :
        return 'base_dev.html'

    @property
    def template_data(self) :
        template_data = self._template_data
        # in development mode, copy assets and data to the report directory
        # instead of writing into the file

        json_str = self.json

        # write the data into its own javascript file
        data_path = os.path.join(self.json_dir,'data.js')
        template_data['data_path'] = 'json/data.js'
        with open(data_path,'w') as f :
            f.write('var detk = detk || {};')
            f.write('detk.data = {};'.format(
                        json.dumps(json_str,indent=2)
                    )
            )

        # format the report
        # do a scan through the json directory to pick up all the existing
        # reports
        module_names = set()
        for module in json_str :
            module_names.add(module.get('name'))

        # load the module templates for the modules found in the report dir
        for asset in ('js','css','html') :

            dest_dir = pathlib.Path(os.path.join(self.report_dir,asset))
            dest_dir.mkdir(parents=True, exist_ok=True)

            # common assets
            common_path = 'templates/{}/common.{}'.format(asset,asset)
            if pkg_resources.resource_exists('de_toolkit',common_path) :
                template_data['common'][asset] = \
                    pkg_resources.resource_string('de_toolkit',common_path).decode()
                # copy the asset
                #shutil.copy(
                #    pkg_resources.resource_filename(
                #        'de_toolkit',common_path
                #    ),
                #    os.path.join(self.report_dir,asset,os.path.basename(common_path))
                #)
                # give the relative path to the asset
                #template_data['common'][asset] = '{}/{}'.format(
                #        asset,
                #        os.path.basename(common_path)
                #)

            # module templates, loaded in as in production mode
            d = template_data['templates'][asset] = {}
            for name in module_names :
                tmpl_path = 'templates/{}/{}.{}'.format(asset,name,asset)
                if pkg_resources.resource_exists('de_toolkit',tmpl_path) :
                    template_data['templates'][asset][name] = \
                        pkg_resources.resource_string('de_toolkit',tmpl_path).decode()
            # third party assets, copied as files instead of inserted into the
            # page
            template_data['assets'][asset] = {}
            asset_dir = 'templates/{}/assets/'.format(asset)

            if pkg_resources.resource_isdir('de_toolkit',asset_dir) :

                for tmpl_path in walk(asset_dir) :
                    dest_path_str = tmpl_path.replace('templates/','')
                    dest_path = pathlib.Path(os.path.join(self.report_dir,dest_path_str))
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    # copy the asset
                    shutil.copy(
                        pkg_resources.resource_filename('de_toolkit',tmpl_path),
                        dest_path
                    )
                    # give the relative path to the asset
                    #rel_path = tmpl_path.replace('assets/','')
                    #template_data['assets'][asset][rel_path] = dest_path_str

        return template_data

def main(argv=sys.argv) :

    if '--version' in argv :
        from .version import __version__
        print(__version__)
        return

    # add the common opts to the docopt strings
    cmd_opts_aug = {}
    for k,v in cmd_opts.items() :
        cmd_opts_aug[k] = _cli_doc(v)

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts) :
        docopt(_cli_doc(__doc__))
    argv = argv[1:]
    cmd = argv[0]

    if cmd == 'generate' :
        args = docopt(cmd_opts_aug['generate'],argv)

        report_class = DetkReport
        if args['--dev'] :
            report_class = DetkReportDev

        # the context manager loads and writes, do nothing inside
        with report_class(args['--report-dir']) :
            pass
    elif cmd == 'clean' :
        args = docopt(cmd_opts_aug['clean'],argv)
        shutil.rmtree(args['--report-dir'],ignore_errors=True)

if __name__ == '__main__' :

    main()
