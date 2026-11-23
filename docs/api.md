# API reference

The primary interface to detk is the command line, but the underlying Python
modules can be used directly. From 1.0 the command line, with what its
`--help` states (its sections, each argument's metavar, default and choices,
and its examples, though not its wording) and its exit codes, is the stable
surface that follows semantic versioning; the Python API below is usable but
not yet a compatibility promise (see [Stability](index.md#stability)). The
core objects:

## Common

::: de_toolkit.common.CountMatrix

::: de_toolkit.common.CountMatrixFile

::: de_toolkit.common.DetkModule

## Reporting

::: de_toolkit.report.DetkReport

::: de_toolkit.report.DetkModuleJSON

## R bridge

::: de_toolkit.wrapr.WrapR

::: de_toolkit.wrapr.wrapr

::: de_toolkit.wrapr.check_r

::: de_toolkit.wrapr.check_r_package
