r"""
Write or remove the detk HTML report: every detk command that runs with a
report directory writes its module JSON there and re-renders the report;
generate renders it again from the module JSON already in the directory, and
clean removes the directory and the provenance crate.
"""

# each subcommand: the one line the command's help lists it with, its
# description and its examples
SUBCOMMANDS = {
    "generate": dict(
        help="Render the HTML report from the module JSON in the report directory",
        description="""\
Render the HTML report (detk_report.html) and the provenance crate again from
the module JSON files the detk commands wrote into the report directory.""",
        examples=[
            ("Render ./detk_report/detk_report.html", "detk-report generate"),
            (
                "Render the report in results/report",
                "detk-report generate --report-dir=results/report",
            ),
        ],
    ),
    "clean": dict(
        help="Remove the report directory and the provenance crate",
        description="""\
Remove the report directory, with the module JSON and the HTML report in it,
and the provenance crate (ro-crate-metadata.json) in the current directory.""",
        examples=[("Remove ./detk_report and the crate", "detk-report clean")],
    ),
}


def build_parser():
    "The detk-report command line parser"
    parser = DetkParser(prog="detk-report", description=__doc__.strip())
    add_command_options(parser)
    subs = add_subcommands(parser)
    for name, spec in SUBCOMMANDS.items():
        sub = subs.add_parser(
            name, help=spec["help"], description=spec["description"], examples=spec["examples"]
        )
        if name == "generate":
            sub.add_argument(
                "--dev",
                action="store_true",
                help="Pretty-print the embedded JSON payload (larger file, easier to read)",
            )
        add_common_options(sub)
    return parser


from collections import OrderedDict
from collections.abc import Mapping
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

from datetime import datetime, UTC

from .common import (
    cli_main,
    _PROCESS_START,
    DetkParser,
    add_command_options,
    add_common_options,
    add_subcommands,
    parse_cli,
    set_logging,
)
from .crate import CRATE_FILENAME, write_crate
from .report_specs import clean, view_for
from .version import __version__

# version of the module JSON document format (the envelope written by
# DetkModuleJSON), major.minor: the major goes up on a backward-incompatible
# change, the minor on an addition every older document still satisfies;
# update module_schema.json to match. 1.1 adds the optional in_file_paths and
# out_file_paths (detk-util record, DETK-0061)
MODULE_SCHEMA_VERSION = "1.1"

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# preferred top-level ordering of module families in the report/nav
FAMILY_ORDER = ["stats", "de", "norm", "transform", "filter", "enrich", "outlier", "other"]


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
                # keys are user data too (sample names, feature IDs): encode
                # them as JSON strings so a quote or backslash stays valid
                key = json.JSONEncoder.encode(self, k if isinstance(k, str) else str(k))
                vals.append(f"{key}: {self.encode(obj[k])}")
            return "{" + ", ".join(vals) + "}"
        return json.JSONEncoder.encode(self, obj)


# characters that could end or alter the HTML <script> block a JSON payload is
# embedded in ("</script>", "<!--"), plus U+2028/U+2029, which old JavaScript
# parsers treat as line breaks; JSON reads the \uXXXX forms back identically
_SCRIPT_JSON_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
    "\u2028": "\\u2028",
    "\u2029": "\\u2029",
}
_SCRIPT_JSON_TRANS = str.maketrans(_SCRIPT_JSON_ESCAPES)


def script_json(obj, indent=None):
    """Serialize ``obj`` as JSON that is safe to embed in an HTML ``<script>``
    element: no string in it can close the element or open markup (#46).

    The escaped characters can only occur inside JSON string literals, so the
    whole serialized text is translated; ``JSON.parse`` (and ``json.loads``)
    return the original strings."""
    return json.dumps(obj, cls=NumpyEncoder, indent=indent).translate(_SCRIPT_JSON_TRANS)


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
        in_file_paths=None,
        out_file_paths=None,
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
                ("end_time", datetime.now(UTC).isoformat()),
                ("argv", list(sys.argv)),
                ("in_file_path", in_file_path),
                ("out_file_path", out_file_path),
                ("column_data_path", column_data_path),
                ("workdir", workdir),
                ("params", module_json["params"]),
                ("properties", module_json["properties"]),
            ]
        )
        # every input and output file of a step with several (schema 1.1);
        # left out otherwise, so other modules' documents are as before
        if in_file_paths is not None:
            self.out_d["in_file_paths"] = list(in_file_paths)
        if out_file_paths is not None:
            self.out_d["out_file_paths"] = list(out_file_paths)

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
        - ``in_file_paths``, ``out_file_paths``: every input and output file,
          for a step with several (optional, schema 1.1)
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
        self,
        module,
        in_file_path=None,
        out_file_path=None,
        column_data_path=None,
        workdir=None,
        in_file_paths=None,
        out_file_paths=None,
    ):
        """Add and serialize the given module to the report directory;
        *in_file_paths* and *out_file_paths* list every input and output
        file of a step with several (detk-util record)"""
        module_json = DetkModuleJSON(
            module,
            in_file_path=in_file_path,
            out_file_path=out_file_path,
            column_data_path=column_data_path,
            workdir=workdir,
            json_dir=self.json_dir,
            in_file_paths=in_file_paths,
            out_file_paths=out_file_paths,
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
            # the payload goes inside <script> elements: escape it so no
            # user string (feature ID, sample name, annotation) can end them
            modules_json=script_json(clean(modules), indent=indent),
            raw_json=script_json(clean(raw), indent=indent),
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


@cli_main
def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    cmd = args.subcommand

    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    if cmd == "generate":
        if args.dev:
            logger.info("pretty-printing embedded JSON due to --dev")
        # standalone generation: collect existing module JSON and render once
        DetkReport(args.report_dir).write(dev=bool(args.dev))

    elif cmd == "clean":
        logger.info("cleaning report dir: %s", args.report_dir)

        shutil.rmtree(args.report_dir, ignore_errors=True)

        # the provenance crate is derived from the report JSON, so it goes too
        if os.path.exists(CRATE_FILENAME):
            logger.info("removing provenance crate: %s", CRATE_FILENAME)
            os.remove(CRATE_FILENAME)

    logger.info("done")


if __name__ == "__main__":
    main()
