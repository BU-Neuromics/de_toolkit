---
kind: step
time: 2026-11-09T18:38:59Z
by: DETK/reviewer
node: release/annotate
step: s2
branch: node/29-annotate
verdict: approve
commits: []
decisions: []
---


# Re-review of PR #41: detk-util annotate, approved

## Summary

I reviewed the PR as it stands at 68a882f (fixes in 1f08601, DETK-0008
revised in 68a882f). I also checked each finding from the first s2 review
against the code and by running the CLI on small hand-made files.

The major finding is fixed. The CLI now reads the result table as text
(`dtype=str, keep_default_na=False`, `de_toolkit/util.py:306`), so Entrez IDs
with a gap no longer turn into floats or crash. `007` stays `007` and matches
`007` but not `7`. Empty or `NA` IDs are never joined: they are counted as
unmapped and reported as `num_missing_ids`, and the report view shows that
count. The minor findings 2, 3, 4 and 8 are fixed as well, and the docs, the
CLI help and the revised DETK-0008 describe the new behaviour accurately.
Findings 5 and 7 are out of scope by the orchestrator's choice and are listed
under Questions as follow-ups.

The fixes broke nothing I could find. All local checks pass, and CI passes
except the R job, which is still pending. The remaining findings are minor
edge cases and none of them blocks the PR.

## Artifacts

- `uv run pytest`: 167 passed, 49 skipped (R not installed locally), 1 warning (from rdflib)
- `uv run ruff check .`: all checks passed
- `uv run ruff format --check .`: 112 files already formatted
- `uv run --group docs mkdocs build --strict`: built clean (only the Material team notice)
- `gh pr checks 41`: CodeQL, docs build (strict), ruff and test on Python 3.10 to 3.13 pass; "test with R (bioconda)" pending
- The diff outside `.cogit/`: CHANGELOG, `de_toolkit/{crate,report_specs,util}.py`,
  `docs/tools/util.md`, `tests/util/test_annotate.py` (19 tests), and
  `.gitignore`. The `.gitignore` line and the `.cogit/` files come from the
  cogit setup commit the branch carries.
- Hand-made CLI runs (`uv run detk-util annotate`):
  - `1,NA,3,007,(empty),3` against an Entrez mapping that has both `007` and
    `7`: no crash, every value written back as read. `007` gets SEVEN, not
    WRONG. `3` gets `A2M;A2Mb` on both rows. The log says "2 result rows have
    an empty or missing ID", and the report JSON has `num_missing_ids: 2`,
    `unmapped_examples: []`, and the "empty or missing IDs" item in the view.
  - `--drop-unmapped` on that file keeps 4 rows, in their order.
  - Versioned IDs with `--strip-versions`, including a duplicated `ENSG2.1`,
    a versioned mapping key (`ENSG2.7`) and RefSeq `NM_1.6`: all joined, and
    the original IDs are kept.
  - A mapping row whose added values are all empty (`ENSG9,,`): unmapped,
    and dropped by `--drop-unmapped`. A row with an empty symbol but an
    Entrez ID counts as mapped only when Entrez is among the added columns.
  - A mapping file with only a header: everything unmapped. With
    `--drop-unmapped` the output is the header only, exit 0.
  - `-i gene` and `-i 1` on `idx,gene,lfc`: the column order is kept, `idx`
    stays first, and the added columns come last.
  - A result whose first column is unnamed (as pandas writes it): it is
    written back unnamed.
  - A result with only a header: the output is the header plus the added
    columns.
  - `-i nope`: a clear error, exit 1.
  - A quoted field containing a comma, and a clash with a result column
    (`desc_annot`): both correct.

## Findings

1. **A result file with a single column is read with the wrong delimiter
   and the output is silently corrupted** (`de_toolkit/util.py:306`).
   Severity: minor. The csv sniffer cannot find a delimiter in a file with
   one column, so it guesses a letter from the header. The file `id` /
   `ENSG1` / `ENSG3` came out with the header `,d,symbol,entrez`. The file
   `gene_id` / … came out as `g,n,_id,symbol,entrez`, with empty columns
   added. The IDs survive here only because they do not contain the guessed
   letter. A bare list of gene IDs (for example the significant genes) is a
   plausible thing to annotate, and the run exits 0. The cause is the
   `sep=None` sniffing that detk uses everywhere (`common.py:308`,
   `enrich.py:386`), and the first review missed it. It could be fixed here
   by falling back to a single column when the result has one header field,
   or in a follow-up. It does not block this PR.
2. **The missing-ID test strips whitespace, but the join does not**
   (`de_toolkit/util.py:227-228`). Severity: nit. ` NA ` counts as a missing
   ID, but ` 007` and `007 ` do not match `007`. The warning prints them with
   their spaces, so the user can see why. Either strip both sides or neither.
3. **A renamed column can clash again** (`de_toolkit/util.py:241`).
   Severity: nit. If the result already has both `symbol` and `symbol_annot`,
   the output has two columns named `symbol_annot`. This is rare and not
   worth a change before 1.0. It could be noted in DETK-0008's consequences.
4. **`num_multimapped` counts mapping rows, not distinct values**
   (`de_toolkit/util.py:238`). Severity: nit. If an ID has two identical
   mapping rows, it counts toward "several mapping rows" even though its
   collapsed value is a single symbol. The label is literally true, so no
   change is needed.

Earlier findings:

| # | Earlier finding | Status |
|---|---|---|
| 1 | major: numeric IDs | fixed, tested (CLI gap, leading zeros, missing/empty, library float IDs), verified by hand |
| 2 | empty mapped value counted as mapped | fixed (a mapping row needs a non-empty added value); documented and tested |
| 3 | duplicate unmapped examples | fixed (`drop_duplicates`); counts stay per row, as documented |
| 4 | `-i` reorders columns | fixed rather than documented: the first column stays the index and the order is kept; tested |
| 5 | mapping file is not an RO-Crate input | out of scope by choice; `mapping_fn` is still in params; see Questions |
| 6 | `crate.py` outside scope | unchanged, still justified |
| 7 | `modules_json\|safe` in `<script>` | out of scope by choice; see Questions |
| 8 | test gaps | fixed: 19 tests, now covering duplicate IDs, a header-only mapping, numeric and missing IDs |

## Questions

- DETK-0008 was revised by the developer (still Provisional, authority
  DETK/developer). It now also commits the 1.0 output to these rules: the
  result is written back as text, the first column stays the index, "mapped"
  needs a non-empty added value, and `num_missing_ids` is reported. These
  rules are sound. Together with `;` and `_annot`, they are a promise about
  the stable surface (DETK-0001), so the human should accept them explicitly
  at s3.
- Follow-up: open an issue for listing the mapping file as an RO-Crate
  input (earlier finding 5).
- Follow-up: open an issue for the report template's
  `{{ modules_json|safe }}` inside `<script>`. `json.dumps` does not escape
  `</`, so a user-supplied ID can end the script block (earlier finding 7).
- Follow-up: should detk's sniffed readers handle a file with one column
  (finding 1)? This affects more than annotate.
- Ensembl PAR IDs (`ENSG….5_PAR_Y`) are still not touched by
  `--strip-versions`. Is a sentence in the docs worth it?
