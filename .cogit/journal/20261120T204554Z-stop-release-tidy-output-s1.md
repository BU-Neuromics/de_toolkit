---
kind: stop
time: 2026-11-20T20:45:54Z
by: adamlabadorf
node: release/tidy-output
branch: node/114-tidy-output
---

# release/tidy-output s1: tidy writes the sheet as read and records

## Done

tidy -p/tidy-covs write the sample sheet with its own header, columns and values; tidy, tidy-counts, tidy-covs record in the report and the crate; quantifiers tutorial uses tidy -p and lists tidy in the crate; tests; CHANGELOG; PR opened

## Stopped because

node acceptance; the tutorial's workaround and the help's report promise

## Next

DETK-0230 (util-family report view for tidy, carried on the branch) needs acceptance, then s1 ticks and @reviewer s2

## Open questions

DETK-0230 Proposed
