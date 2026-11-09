---
kind: step
time: 2026-11-09T20:54:38Z
by: DETK/developer
node: release/quickstart-figure
step: s1
branch: node/59-quickstart-figure
verdict: done
commits: [630bb53]
decisions: []
---

# Done: Redraw the SVG with detk-util gather, regenerate the PNG; open the PR

## Summary

Redrew the first step of docs/simple_pipeline.svg as a solid detk box reading 'detk-util gather' (was a faded csvgather box with a bitbucket.org link; faded means 'not in detk' per the figure's legend), label centred like the other one-line boxes, rest of the SVG untouched. Re-rendered docs/simple_pipeline.png at 629x846 from the SVG with resvg (resvg-py via uv) using Ubuntu and Ubuntu Mono 0.80; the system Ubuntu Mono 0.862 is wider and overflows the boxes, and cairosvg also misplaced the title. The old SVG rendered the same way matches the old Inkscape PNG up to antialiasing; the new PNG differs from it only inside the gather box. docs/quickstart.md already references simple_pipeline.png. mkdocs --strict builds; pytest 275 passed, 49 skipped. Done: acceptance met.

## Artifacts

## Findings

## Questions
