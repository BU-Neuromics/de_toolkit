---
kind: step
time: 2026-11-09T20:56:28Z
by: DETK/reviewer
node: release/quickstart-figure
step: s2
branch: node/59-quickstart-figure
verdict: approve
commits: []
decisions: []
---


# Review of #61: quickstart figure shows detk-util gather

## Summary

The acceptance is met. In `docs/simple_pipeline.svg` the first step reads `detk-util gather`. There is no csvgather text or bitbucket link left (`grep -ci csvgather` gives 0). The box is drawn solid like the other detk steps, and the faded legend box ("other tool not in detk") still applies only to the csvcut step, which is correct. The SVG diff touches only group g3244: the `opacity:0.5` is gone, the second (link) text line is removed, and the label's y moves from 50.12 to 52.65 so a single line sits centred in the box. Nothing else in the SVG changed.

The PNG keeps its 629x846 size and is still 8-bit RGBA, with transparent corners outside the rounded frame (158 vs 168 fully transparent pixels, which is antialiasing). The image matches the quickstart text: step 1 is `detk-util gather`, linked as tools/util.md#gather, and the Snakemake `gather_counts` rule uses `detk-util gather`. Steps 2-8 and the figure's later boxes are unchanged and still agree with the text.

The render reproduces exactly. I ran the developer's `render_resvg.py` with the same fonts on the branch SVG and got a file byte-identical to the committed PNG. Rendering the old SVG the same way and comparing it with the new PNG, every strong pixel difference falls in the gather box (x 146-411, y 126-165). Compared with the old Inkscape PNG, the new file also has small antialiasing and hinting differences across the whole image. The most visible is the sans-serif labels, which come out a shade lighter. You only notice this in a zoomed side-by-side; nothing moves, wraps or overflows.

## Artifacts

- Old and new PNGs, 2x crops (header and gather box, middle section, legend), and my own re-render: /tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rv61/
- `uv run --group docs mkdocs build --strict` passes. The built quickstart/index.html has `<img alt="simple pipeline" src="../simple_pipeline.png">`, and site/simple_pipeline.png is identical to docs/simple_pipeline.png.
- `gh pr checks 61`: ruff, docs build (strict), tests on Python 3.10, 3.12 and 3.13, and CodeQL all pass. When I recorded this, `test (python 3.11)` had since passed and `test with R (bioconda)` was still pending. Neither can be affected by a docs-only change.

## Findings

1. docs/simple_pipeline.svg:19-21 / docs/simple_pipeline.png (low): the repo does not say how to regenerate the PNG. The working recipe (resvg-py, Ubuntu plus Ubuntu Mono 0.80 rather than the system 0.862, at dpi 72.024597, from the SVG's own `inkscape:export-xdpi`) is only in a scratch script and the PR body. Anyone who edits the SVG next and exports with the system fonts will get overflowing labels. Proposed decision for the human: record the recipe in the repo, for example as an XML comment in the SVG or a short docs/dev note, or accept it as it is. This does not block, since the PNG is correct and changes to the figure are rare.
2. docs/simple_pipeline.png (nit): the re-render drops the PNG's pHYs (dpi) and Software metadata chunks that the Inkscape export had. Browsers and mkdocs ignore them, so the displayed size is unchanged. No action needed.
3. docs/simple_pipeline.png (nit): resvg's text antialiasing is slightly lighter than Inkscape's across the whole figure, not only in the changed box. It is visible only zoomed in and is acceptable. Any later re-render with the same recipe will match.

## Questions

- Should the regeneration recipe live in the repo (Finding 1)? That is the human's call; I recommend a one-paragraph comment in the SVG.
