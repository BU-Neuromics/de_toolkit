---
kind: step
time: 2026-11-20T14:35:02Z
by: DETK/developer
node: release/size-factors
step: s1
branch: node/86-size-factors
verdict: done
commits: [2baa18a]
decisions: []
---

# Done: Write the size factors file from `self.size_factors` with tests, update the cli-pin row, check the example and the skill describe it; CHANGELOG; open the PR

## Summary

DESeq2Norm.write_size_factors writes self.size_factors to --size-factors=FILE: tab separated, one row per sample (name, size factor), counts-file column order, names as written, values with repr so they equal the module JSON's properties.size_factors exactly; written only with the option; unwritable path exits 1. Tests in tests/norm (zero-padded unsorted names; file == module == JSON; counts output and JSON unchanged; nothing extra without the option) and an R-gated test against DESeq2::estimateSizeFactors; cli-pin behaviour now 'writes the file'; docs/example.md and run.sh say what the file holds; commands.md usage unchanged; CHANGELOG under Fixed. Decision within the node: no header line, as the help and acceptance describe a two-column file with one row per sample (R: read.delim(f, header=FALSE, row.names=1)); a sample/size_factor header was considered and rejected as a change to the documented format.

## Artifacts

## Findings

## Questions
