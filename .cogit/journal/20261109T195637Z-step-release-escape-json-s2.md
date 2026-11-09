---
kind: step
time: 2026-11-09T19:56:37Z
by: DETK/reviewer
node: release/escape-json
step: s2
branch: node/46-escape-json
verdict: approve
commits: []
decisions: []
---


# Review of #55: the script-block escape is correct and complete; the innerHTML gap is wider than DETK-0014 lists and needs its own follow-up

## Summary

The change does what the node asks. `report.script_json` (de_toolkit/report.py:112-130) serializes with `NumpyEncoder` and then maps `<`, `>`, `&`, U+2028 and U+2029 to `\uXXXX`. Every byte that can end or alter a `<script type="application/json">` element (`</script`, `<!--`, `<script`) needs a `<`. In NumpyEncoder output `<` can only appear inside a JSON string literal, never in numbers, `NaN`/`null`/`true` or punctuation, so translating the whole text is safe, and `JSON.parse`/`json.loads` read the `\u` forms back as the original characters. Escaping `<` alone would be enough. `>` and `&` add defence in depth, and U+2028/2029 are already `\u`-escaped by `ensure_ascii`, so those two entries cost nothing. The key-encoding fix (report.py:103) makes a sample name with `"` or `\` used as a dict key valid JSON. Both `--dev` (indented) and compact output are covered by the parametrized test.

I generated a real report from hostile CLI inputs. On this branch it has exactly 6 script elements, no `<`, `>` or `&` in either payload, a payload that round-trips, and 9 cards built by the page's own JS in jsdom with no injected elements. The same module JSON rendered with `origin/main` collapses to 1 JSON script element, 0 cards and 20 live `<img onerror>` elements. The acceptance criterion is met, with a test.

The remaining path, descriptor text fields inserted with `innerHTML`, is real, and it is wider than DETK-0014 lists (finding 1). It is not a blocker for this node:

- It is a different sink. It cannot end the script block, which is this node's objective.
- No feature ID, sample name or annotation value reaches it from the current CLI. Annotate's note is escaped. Feature IDs and sample names only go to Vega, which draws them on canvas.
- Closing it means editing `report_specs.py` and choosing between text and HTML descriptors (DETK-0014 options C and D). Both are outside this node's scope and are a human's choice.

It should be a tracked follow-up before 1.0.

## Artifacts

- Real report from hostile CLI inputs. Sample names include `s1</script><img src=x onerror=alert(1)>`, `s2"q\b`, `s3<U+2028>x` and `s4<!--`. Feature IDs include `g1</script><img ...>` and `g2&amp;`. A covariate level holds `A</script><img ...>`. An annotate mapping column and its values hold `sym</script><img ...>`, and an unmapped ID holds `unmapped</script><img ...>`. The filter command is `mean(all)>1 and zero(all)<1`. Commands run: `detk-stats summary`, `detk-filter`, `detk-norm deseq2` and `detk-util annotate`, each with `--report-dir`, then `detk-report generate`.
  - Branch: `scratchpad/rv55/report/detk_report.html` has 6 `<script` and 6 `</script`. Neither payload contains `<`, `>` or `&`. `json.loads` returns the hostile names unchanged, for example `"s1</script><img src=x onerror=alert(1)>"` → original. In jsdom, the page's script builds 9 cards, finds 0 `img[onerror]` and fires no alert. Annotate's note shows as escaped text.
  - Same JSON rendered with `origin/main` code (`scratchpad/rv55/report_main/`): 1 JSON script element, 0 cards, 20 `img[onerror]` elements in the document. This reproduces #46.
- Gap probe: module JSON written by hand into a report dir (`scratchpad/rv55/report_gap/`) and rendered on this branch. In jsdom, 4 `img[onerror]` elements are injected, all through `innerHTML`:
  - the filtercounts note (`filter command: mean(all) > 1 <img ...>`)
  - the DE "capped" note through a term name (`cond<img ...>: 2 of 10`)
  - the fallback `<h2>` title and the button text for a module with an unknown `name`

  The `error` path rendered `chart error: list index out of range`, with no user data in it for that trigger.
- Checks:
  - `uv sync` ok.
  - `uv run pytest`: 219 passed, 49 skipped.
  - `uv run ruff check .`: all checks passed.
  - `uv run ruff format --check .`: 163 files already formatted.
  - `uv run --group docs mkdocs build --strict`: built.
  - `gh pr checks 55`: CodeQL, docs, ruff and test 3.10 to 3.13 pass. `test with R (bioconda)` was still pending at review time. The change touches no R path.

## Findings

1. **Medium (follow-up, not this node).** DETK-0014's list of unescaped `innerHTML` fields is incomplete. It names `build_filtercounts`' note (de_toolkit/report_specs.py:322) and the raw-fallback `error` (report_specs.py:960). Two more paths exist:
   - **DE term names**, which carry the user's factor levels. logistf and DESeq2 coefficient names are built with `check.names=FALSE`. The names go raw into the "capped" note (report_specs.py:659, joined at :705-709) and the static-SVG note (report_specs.py:674, `!r` keeps `<`). This is the most reachable of the four: a DE run with more points than the budget and a level like `A<img ...>` will inject markup.
   - **The unknown-module fallback** (report_specs.py:965): `name` becomes the card `<h2>` and button text through the template's `innerHTML` (de_toolkit/templates/report.html:162-168).

   The filtercounts note is barely reachable from the CLI. The ply lexer rejects everything but words, numbers, brackets and comparison operators, and a command that does not parse aborts before the module JSON is written. It is reachable only through hand-written module JSON. The template sinks are report.html:163, 175, 185-186, 190-192 and 197. Recommendation: the follow-up node should take DETK-0014 option C (the page treats descriptor text as text, and `build_annotate` drops its `html.escape`). It should include DE term names in its tests, and DETK-0014's Consequences should list these paths when it is accepted.
2. **Low.** `NumpyEncoder` keys that are not strings are stringified with `str(k)` (report.py:103). `True` and `None` keys become `"True"` and `"None"`, while `json.dumps` would give `"true"` and `"null"`. This keeps the old `f"{k}"` behaviour, so it is not a regression, and no current module uses such keys. Noted only for the record.
3. **Info.** The test checks the escape structurally (a regex for `</script` plus `json.loads`). It does not run the page's JS. That is adequate here, because `JSON.parse` and `json.loads` agree on `\uXXXX` and the jsdom run above confirms it in practice. If the follow-up changes how the page renders, a small jsdom or Playwright smoke test would be worth having.

## Questions

- Should the follow-up for the `innerHTML` path be a new node, taking DETK-0014 option C and covering DE term names and the unknown-module title as well as the two fields DETK-0014 names, scheduled before 1.0? This is the human's call at s3 or in planning. I have not recorded a decision.
- `test with R (bioconda)` was pending when I checked. Wait for it to go green before accepting.
