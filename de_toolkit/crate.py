"""
Process Run Crate emitter.

Writes an ``ro-crate-metadata.json`` describing every recorded detk tool
invocation as standards-conformant provenance, following the Workflow Run
RO-Crate *Process Run Crate* profile (https://w3id.org/ro/wfrun/process/0.5),
which models exactly detk's execution style: individual tools run by hand or
by a script, chained through data lineage (one action's output file is the
next action's input) -- an "implicit workflow".

The crate is a second, standards-facing view of the same facts recorded in the
module JSON documents under ``<report_dir>/json/``:

- each module document becomes a ``CreateAction`` (with a deterministic
  ``urn:uuid`` derived from the document id, so regeneration is idempotent)
- each detk subtool is a ``SoftwareApplication`` (per-subtool granularity,
  e.g. ``detk-norm deseq2`` and ``detk-norm library`` are distinct entities)
- invocation parameters become ``PropertyValue`` entities in the action's
  ``object`` list, alongside the input files
- input/output files are shared ``File`` entities, so chaining is visible in
  the graph

The crate root is the analysis working directory: file paths are written
relative to it when they fall inside, and as absolute ``file://`` URIs when
they do not. The emitter is hand-rolled (the crate is a single JSON-LD file)
to avoid a runtime dependency; conformance is checked in the test suite.
"""

import json
import os
import pathlib
import uuid
from datetime import datetime, timezone

from .version import __version__

PROFILE_URI = "https://w3id.org/ro/wfrun/process/0.5"
RO_CRATE_SPEC = "https://w3id.org/ro/crate/1.1"
RO_CRATE_CONTEXT = "https://w3id.org/ro/crate/1.1/context"
CRATE_FILENAME = "ro-crate-metadata.json"

_REPO_URL = "https://github.com/BU-Neuromics/de_toolkit"
_DOCS_URL = "https://bu-neuromics.github.io/de_toolkit/"

# module name (lowercased DetkModule subclass) -> (executable, subcommand)
SUBTOOLS = {
    "basestats": ("detk-stats", "basestats"),
    "coldist": ("detk-stats", "coldist"),
    "rowdist": ("detk-stats", "rowdist"),
    "colzero": ("detk-stats", "colzero"),
    "rowzero": ("detk-stats", "rowzero"),
    "entropy": ("detk-stats", "entropy"),
    "pca": ("detk-stats", "pca"),
    "filtercounts": ("detk-filter", None),
    "deseq2norm": ("detk-norm", "deseq2"),
    "librarysize": ("detk-norm", "library"),
    "fpkmcounts": ("detk-norm", "fpkm"),
    "plogcounts": ("detk-transform", "plog"),
    "vstcounts": ("detk-transform", "vst"),
    "rlogcounts": ("detk-transform", "rlog"),
    "deseq2counts": ("detk-de", "deseq2"),
    "flgcounts": ("detk-de", "firth"),
    "fgseares": ("detk-enrich", "fgsea"),
    "pmftransform": ("detk-outlier", "shrink"),
    "shrinkcounts": ("detk-outlier", "shrink"),
    "entropycounts": ("detk-outlier", "entropy"),
}

_ENCODING_FORMATS = {
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
    ".txt": "text/plain",
    ".json": "application/json",
    ".html": "text/html",
    ".gz": "application/gzip",
    ".gmt": "text/tab-separated-values",
    ".rda": "application/octet-stream",
    ".rds": "application/octet-stream",
}


def _tool_label(name):
    "Human-readable tool label for a module name, e.g. 'detk-norm deseq2'."
    exe, sub = SUBTOOLS.get(name, ("detk", name))
    return f"{exe} {sub}" if sub else exe


def _software_id(name):
    exe, sub = SUBTOOLS.get(name, ("detk", name))
    frag = f"{exe}-{sub}" if sub else exe
    return f"{_REPO_URL}#{frag}"


def _action_id(doc_id):
    "Deterministic urn:uuid for a module document id, stable across rebuilds."
    return "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"{_REPO_URL}/run/{doc_id}"))


def _file_ref(path, workdir, crate_root):
    """Crate identifier for *path*: relative POSIX path when the file lies
    under the crate root, absolute file:// URI otherwise."""
    if path is None:
        return None
    base = workdir or crate_root
    abspath = os.path.normpath(os.path.join(base, path))
    rel = os.path.relpath(abspath, crate_root)
    if rel.startswith(".."):
        return pathlib.Path(abspath).as_uri()
    return pathlib.PurePath(rel).as_posix()


def _file_entity(ref, crate_root):
    ent = {"@id": ref, "@type": "File"}
    name = ref.rsplit("/", 1)[-1]
    ent["name"] = name
    fmt = _ENCODING_FORMATS.get(os.path.splitext(name)[1].lower())
    if fmt:
        ent["encodingFormat"] = fmt
    return ent


def _is_local(ref):
    return ref is not None and not ref.startswith("file://")


def build_crate(docs, crate_root):
    """Build the crate JSON-LD (as a dict) for *docs*, a list of module JSON
    documents (as written by DetkModuleJSON), rooted at *crate_root*."""
    files = {}  # ref -> entity, shared across actions so lineage is visible
    software = {}
    actions = []
    param_entities = []

    for doc in sorted(docs, key=lambda d: d.get("last_modified", 0)):
        name = doc.get("name", "unknown")
        doc_id = doc.get("id", name)
        workdir = doc.get("workdir")

        sw_id = _software_id(name)
        if sw_id not in software:
            exe, sub = SUBTOOLS.get(name, ("detk", name))
            software[sw_id] = {
                "@id": sw_id,
                "@type": "SoftwareApplication",
                "name": _tool_label(name),
                "url": _DOCS_URL,
                "softwareVersion": doc.get("detk_version", __version__),
            }

        objects = []
        for key in ("in_file_path", "column_data_path"):
            ref = _file_ref(doc.get(key), workdir, crate_root)
            if ref is not None:
                files.setdefault(ref, _file_entity(ref, crate_root))
                objects.append({"@id": ref})

        params = doc.get("params") or {}
        for key in sorted(params):
            value = params[key]
            if value is None:
                continue
            pid = f"#param-{doc_id}-{key}"
            param_entities.append(
                {
                    "@id": pid,
                    "@type": "PropertyValue",
                    "name": f"{_tool_label(name)} {key}",
                    "value": value
                    if isinstance(value, (str, int, float, bool))
                    else json.dumps(value),
                }
            )
            objects.append({"@id": pid})

        results = []
        ref = _file_ref(doc.get("out_file_path"), workdir, crate_root)
        if ref is not None:
            files.setdefault(ref, _file_entity(ref, crate_root))
            results.append({"@id": ref})

        action = {
            "@id": _action_id(doc_id),
            "@type": "CreateAction",
            "name": f"{_tool_label(name)} run",
            "instrument": {"@id": sw_id},
        }
        if doc.get("start_time"):
            action["startTime"] = doc["start_time"]
        if doc.get("end_time"):
            action["endTime"] = doc["end_time"]
        if objects:
            action["object"] = objects
        if results:
            action["result"] = results
        actions.append(action)

    has_part = [
        {"@id": ref}
        for ref, ent in files.items()
        if _is_local(ref) and os.path.exists(os.path.join(crate_root, ref))
    ]

    root = {
        "@id": "./",
        "@type": "Dataset",
        "conformsTo": {"@id": PROFILE_URI},
        "name": "detk analysis provenance",
        "description": (
            "Provenance of de_toolkit (detk) tool executions in this directory, "
            "recorded as a Process Run Crate. Each CreateAction is one detk "
            "invocation; the same facts in detk's native format are under "
            "the report directory's json/ folder."
        ),
        # detk cannot assert a license over the user's data; RO-Crate allows a
        # textual statement, and the owner may replace it with a license URI
        "license": (
            "Not specified -- rights to the data described by this crate remain with its owner."
        ),
        "datePublished": datetime.now(timezone.utc).isoformat(),
        "hasPart": has_part,
        "mentions": [{"@id": a["@id"]} for a in actions],
    }

    # the profile itself must be present in the graph as a contextual entity
    profile = {
        "@id": PROFILE_URI,
        "@type": "CreativeWork",
        "name": "Process Run Crate",
        "version": PROFILE_URI.rsplit("/", 1)[-1],
    }

    descriptor = {
        "@id": CRATE_FILENAME,
        "@type": "CreativeWork",
        "conformsTo": {"@id": RO_CRATE_SPEC},
        "about": {"@id": "./"},
    }

    graph = [descriptor, root, profile]
    graph.extend(files.values())
    graph.extend(software.values())
    graph.extend(param_entities)
    graph.extend(actions)

    return {"@context": RO_CRATE_CONTEXT, "@graph": graph}


def write_crate(docs, crate_root):
    """Write ro-crate-metadata.json for *docs* at *crate_root*. Returns the
    path written, or None if there are no documents to describe."""
    if not docs:
        return None
    crate = build_crate(docs, crate_root)
    path = os.path.join(crate_root, CRATE_FILENAME)
    with open(path, "w") as f:
        json.dump(crate, f, indent=2)
    return path
