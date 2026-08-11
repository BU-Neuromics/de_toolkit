r"""
Usage:
    detk-report generate [options]
    detk-report clean [options]
"""

cmd_opts = {
    "generate": r"""
Usage:
    detk-report generate [options]

Options:
    --dev  Pretty-print the embedded JSON payload (larger file, easier to read)
""",
    "clean": r"""
Usage:
    detk-report clean [options]
""",
}

from collections import OrderedDict
from collections.abc import Mapping
from docopt import docopt
from glob import glob
import hashlib
from importlib.resources import files as _pkg_files
import jinja2
import json
import logging
from pprint import pformat
import numpy as np
import os
import pathlib
import shutil
import sys
import time

from datetime import datetime, timezone

from .common import _PROCESS_START, _cli_doc, set_logging
from .crate import CRATE_FILENAME, write_crate
from .report_specs import clean, view_for
from .version import __version__

# version of the module JSON document format (the envelope written by
# DetkModuleJSON); bump on any backward-incompatible change and update
# module_schema.json to match
MODULE_SCHEMA_VERSION = "1.0"

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# preferred top-level ordering of module families in the report/nav
FAMILY_ORDER = ["stats", "de", "norm", "transform", "filter", "enrich", "other"]


def _asset(*parts):
    "Read a packaged asset (e.g. a vendored JS file or template) as text."
    t = _pkg_files("de_toolkit")
    for p in parts:
        t = t / p
    return t.read_text(encoding="utf-8")


class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types"""

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):  #### This is the fix
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

    def encode(self, obj):
        if isinstance(obj, float):
            return format(obj, ".3f").replace("nan", "NaN")
        elif isinstance(obj, (list, tuple)):
            return "[" + ", ".join(list(map(self.encode, obj))) + "]"
        elif isinstance(obj, Mapping):
            vals = []
            for k in sorted(obj):
                vals.append(f'"{k}": {self.encode(obj[k])}')
            return "{" + ", ".join(vals) + "}"
        return json.JSONEncoder.encode(self, obj)


def hash_str(st):
    return hashlib.md5(st.encode()).hexdigest()


class DetkModuleJSON:
    def __init__(
        self,
        module,
        in_file_path=None,
        out_file_path=None,
        column_data_path=None,
        workdir=None,
        json_dir=".",
        json_path=None,
    ):

        # the json filename is calculated as the combination of
        # the module name, the parameters passed, and the input filename
        repl_file_path = "-" if in_file_path is None else in_file_path

        # since the parameters is a dictionary, convert to a json string
        # to calculate the hash
        param_str = json.dumps(module.params, sort_keys=True, cls=NumpyEncoder)
        logger.debug("report param string:\n%s", pformat(param_str))

        module_id = hash_str(module.name + param_str + repl_file_path + __version__)
        logger.debug("writing module for module_id: %s", module_id)

        filename = f"{module_id}.json"

        if json_path is not None:
            self.filepath = json_path
        else:
            self.filepath = os.path.realpath(os.path.join(json_dir, filename))
        logger.debug("writing module JSON to: %s", self.filepath)

        if workdir is None:
            workdir = os.getcwd()

        module_json = module.json
        self.out_d = OrderedDict(
            [
                ("name", module.name),
                ("id", module_id),
                ("schema_version", MODULE_SCHEMA_VERSION),
                ("detk_version", __version__),
                ("last_modified", int(1000 * time.time())),
                # start_time approximates process start (module import time);
                # end_time is when the module was recorded
                ("start_time", _PROCESS_START.isoformat()),
                ("end_time", datetime.now(timezone.utc).isoformat()),
                ("argv", list(sys.argv)),
                ("in_file_path", in_file_path),
                ("out_file_path", out_file_path),
                ("column_data_path", column_data_path),
                ("workdir", workdir),
                ("params", module_json["params"]),
                ("properties", module_json["properties"]),
            ]
        )

    def write(self, indent=None):
        """
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
        """

        logger.debug(
            "writing out module JSON for module %s (id: %s)", self.out_d["name"], self.out_d["id"]
        )

        with open(self.filepath, "w") as f:
            json.dump(self.out_d, f, indent=indent, cls=NumpyEncoder)


class DetkReport:
    """
    Collects detk module JSON and renders a single self-contained, offline HTML
    report. Each module run serializes its JSON into ``<report_dir>/json/`` (the
    machine-readable layer); ``write`` assembles every JSON found there into one
    ``detk_report.html`` whose charts are rendered client-side by a vendored,
    no-build Vega-Lite bundle, with the raw JSON embedded for provenance.
    """

    template_name = "report.html"
    vega_assets = ("vega.min.js", "vega-lite.min.js", "vega-embed.min.js")

    def __init__(self, report_dir="./detk_report", crate_dir=None):
        self.report_dir = os.path.realpath(report_dir)
        logger.debug("creating DetkReport at report dir: %s", self.report_dir)

        # the Process Run Crate is rooted at the analysis working directory,
        # so file references in the provenance resolve relative to where the
        # tools ran; pass crate_dir to root it elsewhere
        self.crate_dir = os.path.realpath(crate_dir) if crate_dir is not None else os.getcwd()

        self.json_dir = os.path.join(self.report_dir, "json")
        logger.debug("json dir: %s", self.json_dir)

        pathlib.Path(self.json_dir).mkdir(parents=True, exist_ok=True)
        self.report_path = os.path.join(self.report_dir, "detk_report.html")
        logger.debug("report path: %s", self.report_path)

        self.modules = []

    def add_module(
        self, module, in_file_path=None, out_file_path=None, column_data_path=None, workdir=None
    ):
        "Add and serialize the given module to the report directory"
        module_json = DetkModuleJSON(
            module,
            in_file_path=in_file_path,
            out_file_path=out_file_path,
            column_data_path=column_data_path,
            workdir=workdir,
            json_dir=self.json_dir,
        )
        logger.debug("adding detk module json for module %s", module.name)
        self.modules.append(module_json)

    @property
    def json(self):
        "Serialize pending modules, then load every module JSON in the report dir."
        for module in self.modules:
            logger.debug("writing module JSON: %s", module.out_d.get("name"))
            module.write()

        json_str = []
        for fn in sorted(glob(os.path.join(self.json_dir, "*.json"))):
            logger.debug("found module json: %s", fn)
            with open(fn) as f:
                json_str.append(json.loads(f.read().strip()))

        return json_str

    def build_modules(self):
        "Turn each collected module JSON into a render descriptor for the SPA."
        modules, raw, seen = [], {}, {}
        for mj in self.json:
            family, title, desc, view = view_for(mj)
            base = mj.get("name", "unknown")
            n = seen.get(base, 0)
            seen[base] = n + 1
            dom_id = base if n == 0 else f"{base}-{n}"
            modules.append(
                {
                    "id": dom_id,
                    "module": base,
                    "family": family,
                    "title": title,
                    "desc": desc,
                    "view": view,
                }
            )
            raw[dom_id] = mj

        fam_rank = {f: i for i, f in enumerate(FAMILY_ORDER)}
        modules.sort(key=lambda m: (fam_rank.get(m["family"], len(FAMILY_ORDER)), m["title"]))
        return modules, raw

    def write(self, dev=False):
        logger.debug("writing out report to %s", self.report_path)

        modules, raw = self.build_modules()
        indent = 2 if dev else None

        vega = {
            name.split(".")[0].replace("-", ""): _asset("templates", "vega", name)
            for name in self.vega_assets
        }

        template = jinja2.Template(_asset("templates", self.template_name))
        html = template.render(
            modules_json=json.dumps(clean(modules), cls=NumpyEncoder, indent=indent),
            raw_json=json.dumps(clean(raw), cls=NumpyEncoder, indent=indent),
            vega_js=vega["vega"],
            vegalite_js=vega["vegalite"],
            vegaembed_js=vega["vegaembed"],
        )
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("wrote report (%d modules) to %s", len(modules), self.report_path)

        # standards-facing provenance: a Process Run Crate describing every
        # recorded invocation, rooted at the analysis working directory
        crate_path = write_crate(list(raw.values()), self.crate_dir)
        if crate_path:
            logger.info("wrote provenance crate to %s", crate_path)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.write()


def main(argv=sys.argv):

    if "--version" in argv:
        from .version import __version__

        print(__version__)
        return

    # add the common opts to the docopt strings
    cmd_opts_aug = {}
    for k, v in cmd_opts.items():
        cmd_opts_aug[k] = _cli_doc(v)

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts):
        docopt(_cli_doc(__doc__))
    argv = argv[1:]
    cmd = argv[0]

    if cmd == "generate":
        args = docopt(cmd_opts_aug["generate"], argv)

        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))

        if args["--dev"]:
            logger.info("pretty-printing embedded JSON due to --dev")
        # standalone generation: collect existing module JSON and render once
        DetkReport(args["--report-dir"]).write(dev=bool(args["--dev"]))

    elif cmd == "clean":
        args = docopt(cmd_opts_aug["clean"], argv)

        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))

        logger.info("cleaning report dir: %s", args["--report-dir"])

        shutil.rmtree(args["--report-dir"], ignore_errors=True)

        # the provenance crate is derived from the report JSON, so it goes too
        if os.path.exists(CRATE_FILENAME):
            logger.info("removing provenance crate: %s", CRATE_FILENAME)
            os.remove(CRATE_FILENAME)

    logger.info("done")


if __name__ == "__main__":
    main()
