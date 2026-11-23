---
kind: step
time: 2026-11-23T18:22:59Z
by: DETK/reviewer
node: release/record-program
step: s2
branch: review/record-program
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: from a working directory deep in another tree run detk-util record -- /usr/bin/cp a b and one with a program off PATH, read argv in the module JSON and the crate, and re-run the recorded line

## Summary

Approved: both acceptance items hold under DETK-0390 Option B. Working from a directory five levels deep in a scratch tree, `detk-util record -i a -o b -- /usr/bin/cp a b` is recorded as `cp a b` in params.argv, params.command, detk-util's own argv (`-- cp a b`) and the crate's 'detk-util record command'. A program off PATH (`<tree>/tools/show q`) is recorded as `../../../../../tools/show q` in all three. Running each recorded command from workdir gives the same result: the copies match byte for byte, and show prints 'hi q'. Called directly, program_arg leaves a bare name as typed. When PATH finds a different python3 first (a venv bin/python3 that symlinks to /usr/bin/python3), /usr/bin/python3 stays relative, which is correct because the name would run the other file. The tests cover all the cases the node asks for: by name, re-run, off PATH, PATH finds another file, a bare name typed as such, and only the program word (an absolute cp among the arguments stays relative). record's --help, module_schema.json (argv and params) and the CHANGELOG under Changed state the rule. Locally, tests/util/test_record.py has 42 passed and 1 skipped (R-gated), and the full suite has 2559 passed. Ruff is clean. CI is all green on f04d658, including 'test with R (bioconda)' with 2690 passed, and the branch merges cleanly into origin/main.

On the developer's two calls, I agree with both. (1) Comparing paths after resolving directories, not os.path.samefile, is right. samefile would treat a venv python as the same file as the /usr/bin/python3 it links to, but running it by name gives a different environment, and DETK-0390's criterion is that the recorded line re-runs the same program. The cost is smaller than the developer wrote: on a merged-/usr system (this one) /bin resolves to /usr/bin, so `/bin/cp` is also recorded as `cp`. Only where /bin and /usr/bin are separate directories does /bin/cp stay relative, and the recorded line still re-runs there. (2) Rewriting the top-level argv is required. The acceptance names the embedded report payload, and leaving the ../ chain in argv would leave it in the payload, which I checked. Locating the command as the tail of sys.argv is sound because `--` ends record's options. When sys.argv does not end with the command (an in-process call), the argument is left relative, which is a safe fallback.

No changes asked. No new decisions.

## Artifacts

## Findings

None blocking. A note for release/cli-docs: on a system where /bin and /usr/bin are separate directories, /bin/cp stays relative when PATH finds /usr/bin/cp first. It still re-runs; the docs can say so.

## Questions
