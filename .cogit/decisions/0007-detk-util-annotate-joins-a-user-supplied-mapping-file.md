---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/annotate, step: s1}
applies: [release/annotate]
allowed_by: [reasonable]
reason: "Reproducible offline joins keep detk out of the annotation-database business, as #29 proposes"
---

# detk-util annotate joins a user-supplied mapping file, offline

## Background

detk's differential expression results are keyed by the feature IDs of
the counts matrix, usually Ensembl gene IDs, which nobody can read and
which `detk-enrich fgsea` often cannot match against symbol-keyed GMT
files. Users add gene symbols with ad-hoc pandas or R after the fact.
Issue #29 asks for a `detk-util annotate` subcommand that does this.

## Context

The mapping from IDs to symbols (or Entrez IDs, biotypes, descriptions)
has to come from somewhere. Criteria: a run must be reproducible and
recordable in the report and the RO-Crate provenance; detk must work
offline, on clusters without outbound network, and in CI; the 1.0 CLI
is the stable surface (DETK-0001), so the subcommand name and options
are a promise; and detk should not take on maintaining annotation
databases for many organisms and releases.

## Options

1. **A user-supplied delimited mapping file** (BioMart export, a table
   derived from the GTF used for quantification, an `org.*.db` dump),
   joined on a named or positional column. Reproducible, offline, any
   organism, provenance names the file; the user must obtain the table.
2. **An online service** (biomaRt through wrapr, or mygene.info over
   HTTP). Convenient; but results change with the service's release,
   need network and an extra dependency, and fail in CI and on
   isolated nodes.
3. **Bundled annotation tables** shipped with detk. Offline and
   convenient for human and mouse; but detk would own data releases
   and package size, and other organisms are left out.

## Decision

Option 1, with the interface #29 proposes:
`detk-util annotate [options] <result_fn> <mapping_fn>` with
`-i/--idcol` (default 0), `--map-from` (default 0), `--map-to`
(comma-separated, default `all` = every mapping column but
`--map-from`), `--strip-versions`, `--drop-unmapped`, `-o/--output`.
Columns are named by header or by 0-based position, like the rest of
detk's sniffed delimited inputs. The added columns keep the mapping
file's header names (see DETK-0008 for clashes). Reproducibility and
offline use decided it, and the issue's author asked for it.

## Consequences

- The mapping file's path is recorded in the module JSON's `params`
  (`mapping_fn`); the RO-Crate lists only `in_file_path` and
  `column_data_path` as inputs, so the mapping file is not yet a crate
  input object. Adding it needs a change to `de_toolkit/crate.py`
  outside this node.
- An online lookup can be added later as a separate helper that writes
  a mapping file, without changing `annotate`.
- Revisit if users mostly fail to obtain mapping tables; the docs page
  names the usual sources.
