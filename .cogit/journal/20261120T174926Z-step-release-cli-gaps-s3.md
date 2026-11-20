---
kind: step
time: 2026-11-20T17:49:26Z
by: DETK/developer
node: release/cli-gaps
step: s3
branch: node/95-cli-gaps
verdict: done
commits: [ea2c55e, 8cda6e6]
decisions: []
---

# Done: Generate bash, zsh and tcsh completion with shtab at build time, ship the scripts and the command that prints them, add the regenerate-and-compare test; CHANGELOG

## Summary

Shell completion (DETK-0032): de_toolkit/completions/detk.{bash,zsh,tcsh} generated from the argparse parsers by shtab (python -m de_toolkit.completions._generate) and shipped in the wheel; detk's commands complete as the module commands they run; FILE/DIR and *_fn arguments complete paths; per-script shtab prefixes avoid detk de / detk-de function clashes. shtab in the dev group only (not in the wheel's Requires-Dist; no build hook, the scripts are committed). 'detk completion <shell>' prints the shipped script without shtab, with DETK-0025 help (description says how to load each shell) and exit codes; pinned in tests/cli (prints the file; missing/unknown shell, extra arg, unknown option exit 2; listed in detk help; help sections). tests/completion: regenerate-and-compare per shell, every command and subcommand in each script, bash completes every subcommand/options/choices, detk completion runs with shtab blocked. commands.md and CHANGELOG (Added). zsh and tcsh scripts not exercised in a real shell (not installed locally or in CI); bash is. Local 3.13 and 3.11 full suites pass; runtime-only check passes and detk completion runs under --no-dev. CI green on 8cda6e6.

## Artifacts

## Findings

## Questions
