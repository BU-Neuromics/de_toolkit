---
kind: step
time: 2026-11-20T21:34:45Z
by: DETK/reviewer
node: release/tidy-output
step: s2
branch: review/tidy-output
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: run tidy -p on a real sample sheet and read the file, check the module JSON and the crate, run the quantifiers tutorial

## Summary

Changes asked: the sheet round-trips exactly (001, 1.50, 07, empty cells, quoted commas), counts unchanged, module JSON and crate list tidy's inputs and outputs, tutorial green, CI green incl. R; but a short-header sheet (R write.table layout) with numeric-looking IDs like 001 now fails (worked on main): read_column_data takes pandas' typed RangeIndex for a normal header

## Artifacts

## Findings

Review of PR #119 at c7bbbdc (diff against origin/main).

Checked
- CI is green on c7bbbdc in every job: ruff, 3.11/3.12/3.13, docs build (strict), runtime dependencies only, combined coverage, CodeQL and test with R (bioconda). Locally on 3.13 (uv, no R), the full suite gives 2246 passed, 92 skipped. tests/tutorials gives 35 passed, 1 skipped (the runner's markdown-render test, which needs `markdown`), and the quantifiers page is among those that pass.
- tidy -p on a real sample sheet, read back. The sheet was `sample,condition,dose,note,batch` with rows `002,treat,1.50,,07`, `001,ctrl,0.10,"a, b",` and an extra `ZZ`, against counts `gene,001,002,S3,P1`. -p writes `sample,condition,dose,note,batch / 001,ctrl,0.10,"a, b", / 002,treat,1.50,,07`. The header is kept, there is no counts column, the rows follow the counts' order, and 001, 1.50, 07, empty cells and a quoted comma all come back exactly as read. tidy-covs writes the same. The counts output (`gene,001,002`) matches main byte for byte. R's write.csv layout (`"","condition",...`) works, and its empty first cell stays empty. A sheet with its own counts column keeps it (tested). Duplicate sample rows behave as on main.
- Module JSON: the name is tidy/tidycounts/tidycovs and params is {}. properties holds the kept and dropped samples. in_file_paths is [counts, sheet] and out_file_paths is [-o, -p]. column_data_path is the sheet. --no-report writes nothing.
- Crate: "detk-util tidy run" has instrument #detk-util-tidy, object [counts.csv, samples.csv] and result [ct.csv, st.csv]. crate.py maps all three subcommands.
- Report view (DETK-0230): a util-family kv card (samples kept, counts/column data samples, features, dropped samples as a plain-text note), with a raw fallback when properties are missing. Both are tested.
- Tutorial: it uses tidy -p, uses samples_tidy.csv downstream, and lists "detk-util tidy run" in the crate's steps. The expect block was updated, and the page passes under the harness.
- CHANGELOG has two entries under Fixed, which are accurate.
- The shared help ("Directory to write the HTML report and module JSON into" / "Do not write the HTML report") now matches what tidy does.

Change asked
1. Regression: a sample sheet whose header is one field short breaks tidy when the sample IDs look numeric. This is R's write.table(sep=",") layout, with no header cell over the row names. Repro: counts `gene,001,002,S3,P1`, and sheet `"condition","dose"` / `"001","ctrl","1.50"` / `"002","treat",""`. `detk-util tidy -o a.csv -p b.csv counts.csv sheet.csv` fails with "No sample names were found to be in common". On origin/main the same command succeeds and matches 001 and 002. The cause is in read_column_data (util.py). With engine="python" and dtype=str, pandas types the implicit index anyway, so 001 and 002 become 1 and 2 in a RangeIndex(1, 3). The `isinstance(table.index, pandas.RangeIndex)` check then takes it for a normal header, and the code set_index()es the condition column. The IDs are lost and lose their zeros, and the comment's "header one field short" branch is never reached for numeric IDs. Sheets with IDs like 1,3,7 hit the same misparse (on main those failed too, though for a different reason). Fix: don't decide the layout from the index type. Read the first field of every line as text, the way read_id_table does in common.py (`header=None, usecols=[0], dtype=str`), or compare the header's field count to the first data row's. Then index by those IDs, with the index name empty for a short header. Add a tests/util/test_tidy.py case with a short-header sheet and IDs 001/002, checking that -p writes the IDs as written and tidy matches them.

Not blocking
- A sheet with a single column and a quoted header (`"condition"` / `"S1","a"`) fails in the delimiter sniffing ("'' expected after '\"'"). This happens before the tidy code runs, is probably pre-existing, and is outside this node's scope.
- The crate goes to the working directory whatever --report-dir is (as designed and documented), so two tidy runs with different report dirs overwrite each other's crate. This is pre-existing and not this node's to change.

## Questions
