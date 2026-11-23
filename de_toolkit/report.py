r"""
Write or remove the detk HTML report: every detk command that runs with a
report directory writes its module JSON there and re-renders the report;
generate renders it again from the module JSON already in the directory, and
clean removes the directory, and the provenance crate in it, with it.
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
        help="Remove the report directory, with its provenance crate",
        description="""\
Remove the report directory, with the module JSON, the HTML report and the
provenance crate (ro-crate-metadata.json) in it. A ro-crate-metadata.json an
earlier detk version wrote into the current directory is left alone.""",
        examples=[("Remove ./detk_report and the crate in it", "detk-report clean")],
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
import math
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
from .crate import CRATE_FILENAME, STDOUT_MARKER, finite_json, write_crate
from .report_specs import clean, view_for
from .version import __version__

# version of the module JSON document format (the envelope written by
# DetkModuleJSON), major.minor: the major goes up on a backward-incompatible
# change, the minor on an addition every older document still satisfies;
# update module_schema.json to match. 1.1 adds the optional in_file_paths and
# out_file_paths (detk-util record, DETK-0061); 1.2 records workdir relative
# to the report directory, argv[0] as the command's name and the file paths
# relative to workdir (DETK-0280). A 1.1 document's absolute workdir still
# resolves the same way: joined to the report directory, it is itself
MODULE_SCHEMA_VERSION = "1.2"

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
    """JSON encoder for module JSON: numpy scalars and arrays become their
    Python values, and a non-finite number (NaN, inf, -inf), at any nesting
    level, is written as null. The output is always strictly valid JSON: the
    encoder runs with ``allow_nan=False``, so a bare ``NaN`` or ``Infinity``
    can never be written (#116)."""

    def __init__(self, *args, **kwargs):
        kwargs["allow_nan"] = False
        super().__init__(*args, **kwargs)

    def default(self, obj):
        # finite_json has already turned numpy scalars and arrays into Python
        # values; this is the fallback for anything reaching the encoder
        # without it
        if isinstance(obj, (np.integer, np.floating, np.bool_, np.ndarray)):
            return finite_json(obj)
        return json.JSONEncoder.default(self, obj)

    def iterencode(self, o, _one_shot=False):
        # json.dump goes through iterencode, json.dumps through encode (which
        # ends here for anything but a float, list or mapping)
        return super().iterencode(finite_json(o), _one_shot)

    def encode(self, obj):
        if isinstance(obj, float):
            if not math.isfinite(obj):
                return "null"
            return format(obj, ".3f")
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


def _relpath(path, start):
    """*path* relative to the directory *start*, as a POSIX path; *path*
    unchanged when it has no relative form (another Windows drive)"""
    try:
        return pathlib.PurePath(os.path.relpath(path, start)).as_posix()
    except ValueError:
        return path


def _file_relpath(path, workdir):
    """A file path as recorded in module JSON: relative to *workdir* (an
    absolute directory), whether it was typed relative or absolute (DETK-0280).
    None, ``-`` (a standard stream) and anything not a string are kept, and
    so is ``stdout``, the marker of a result written to standard output; a
    file in *workdir* really named stdout (``./stdout``, or typed absolute)
    is written ``./stdout``, so it is not read as the marker."""
    if not isinstance(path, str) or path in ("", "-", STDOUT_MARKER):
        return path
    if os.path.isabs(path):
        # resolve the directories (/tmp and /private/tmp are one), not the
        # file itself: a symlinked file keeps the name it was given
        head, tail = os.path.split(path)
        path = os.path.join(os.path.realpath(head), tail)
    rel = _relpath(os.path.normpath(os.path.join(workdir, path)), workdir)
    return "./" + rel if rel == STDOUT_MARKER else rel


def _is_path(text):
    """Whether *text*, typed as an argument, is taken for an absolute path.
    An absolute path that exists (``os.path.lexists``) is one, whitespace or
    not (DETK-0590), so ``/home/me/proj/My Data/c.csv`` is. Otherwise, as
    DETK-0580 says, it starts with ``/`` (or a drive), has no whitespace,
    and its parent directory exists. So a shell script, an awk program or a
    regular expression that starts with ``/`` (``/usr/bin/env echo hi``,
    ``/^gene/ {print}``, ``/^g1,/``) is not, while an output not yet written
    (``/home/me/proj/out.csv``, its directory there) is."""
    if not os.path.isabs(text):
        return False
    if os.path.lexists(text):
        return True
    return not any(c.isspace() for c in text) and os.path.isdir(os.path.dirname(text))


def relative_arg(arg, workdir):
    """A command line argument as recorded (DETK-0281): an absolute path is
    written relative to *workdir* (an absolute directory), as the value of
    ``--opt=/abs/path`` or of a short option given with it (``-o/abs/path``)
    is; any other argument is kept as typed. An argument is taken for an
    absolute path only as :func:`_is_path` says (DETK-0580, DETK-0590), so
    one that merely starts with ``/`` is kept. The command line then re-runs the same
    from *workdir*."""
    if not isinstance(arg, str) or not arg:
        return arg
    if _is_path(arg):
        return _file_relpath(arg, workdir)
    if arg.startswith("--") and "=" in arg:
        opt, value = arg.split("=", 1)
        if _is_path(value):
            return f"{opt}={_file_relpath(value, workdir)}"
    elif arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
        if _is_path(arg[2:]):
            return arg[:2] + _file_relpath(arg[2:], workdir)
    return arg


def relative_argv(argv, workdir):
    "Every argument of *argv* as :func:`relative_arg` records it"
    return [relative_arg(a, workdir) for a in argv]


def _resolved(path):
    "*path* absolute, its directories resolved and the file keeping its name"
    head, tail = os.path.split(os.path.abspath(path))
    return os.path.join(os.path.realpath(head), tail)


def program_arg(program, workdir):
    """The program of a command line as recorded (DETK-0390 Option B): typed
    as an absolute path, it is written as its bare name when PATH finds that
    same file by that name (``/usr/bin/cp`` is ``cp``), as a detk command's
    ``argv[0]`` is its name; otherwise as :func:`relative_arg` writes it, so
    the command line re-runs the same from *workdir* either way."""
    if isinstance(program, str) and os.path.isabs(program):
        name = os.path.basename(program)
        found = shutil.which(name) if name else None
        if found is not None and _resolved(found) == _resolved(program):
            return name
    return relative_arg(program, workdir)


def _argv(workdir, command=None):
    """The process argument vector as recorded: argv[0] the command's name
    only, an absolute path among the arguments relative to *workdir*. When
    the process ran *command* (detk-util record, the words after ``--``,
    which end the vector), its program is written by :func:`program_arg`."""
    argv = list(sys.argv)
    if argv:
        rest = argv[1:]
        n = len(command) if command else 0
        at = len(rest) - n if n and rest[len(rest) - n :] == list(command) else None
        argv = [os.path.basename(argv[0])] + relative_argv(rest, workdir)
        if at is not None:
            argv[1 + at] = program_arg(rest[at], workdir)
    return argv


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
        report_dir=None,
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

        # recorded paths name no directory of this machine (DETK-0280):
        # workdir relative to the report directory, the file paths relative
        # to workdir
        if report_dir is None:
            report_dir = os.path.dirname(os.path.realpath(json_dir))
        report_dir = os.path.realpath(report_dir)
        workdir = os.path.realpath(os.getcwd() if workdir is None else workdir)

        def rel(path):
            return _file_relpath(path, workdir)

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
                ("argv", _argv(workdir, getattr(module, "command_argv", None))),
                ("in_file_path", rel(in_file_path)),
                ("out_file_path", rel(out_file_path)),
                ("column_data_path", rel(column_data_path)),
                ("workdir", _relpath(workdir, report_dir)),
                ("params", module_json["params"]),
                ("properties", module_json["properties"]),
            ]
        )
        # every input and output file of a step with several (schema 1.1);
        # left out otherwise, so other modules' documents are as before
        if in_file_paths is not None:
            self.out_d["in_file_paths"] = [rel(p) for p in in_file_paths]
        if out_file_paths is not None:
            self.out_d["out_file_paths"] = [rel(p) for p in out_file_paths]

    def write(self, indent=None):
        """
        Write out the module JSON to file.

        Each JSON file has one top level object with the following properties:
        - ``name``: name of the module
        - ``id``: machine readable ID
        - ``detk_version``: version of detk that generated this file
        - ``last_modified``: local system timestamp in milliseconds when this
          file was created/modified
        - ``argv``: the command line, ``argv[0]`` the command's name only and
          an absolute path among the arguments relative to ``workdir``
        - ``workdir``: the directory where detk was run, relative to the
          report directory (``..`` for the default ``./detk_report``)
        - ``in_file_path``: path to the file that was processed
        - ``out_file_path``: path to the file that was output, if available
        - ``column_data_path``: path to the column data file used, if available
        - ``in_file_paths``, ``out_file_paths``: every input and output file,
          for a step with several (optional, schema 1.1)

        Every file path is relative to ``workdir`` (schema 1.2, DETK-0280).
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

        # the Process Run Crate goes with the report and is rooted in the
        # report directory (DETK-0280), so each report has its own and its
        # file references resolve from where it sits; pass crate_dir to
        # root it elsewhere
        self.crate_dir = os.path.realpath(crate_dir) if crate_dir is not None else self.report_dir

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
            report_dir=self.report_dir,
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
        # recorded invocation, rooted in the report directory
        crate_path = write_crate(list(raw.values()), self.crate_dir, report_dir=self.report_dir)
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

        # the provenance crate is in the report directory and goes with it;
        # a ./ro-crate-metadata.json an earlier version wrote is left alone
        shutil.rmtree(args.report_dir, ignore_errors=True)
        if os.path.exists(CRATE_FILENAME):
            logger.info(
                "leaving %s in the current directory: detk now writes the crate "
                "into the report directory",
                CRATE_FILENAME,
            )

    logger.info("done")


if __name__ == "__main__":
    main()
