"""
Test cases generated from ``cli_tables.py``: a command line for every
positional, every option in each of its forms and every default, and the
invalid command lines every subcommand rejects.
"""

import pytest

from cli_tables import COMMANDS, COMMON, Bad, Line


def prefix(command, sub):
    "The command line up to the subcommand's arguments"
    return (command.prog,) + ((sub.name,) if sub.name else ())


def options(sub):
    return sub.options + COMMON


def defaults(sub):
    "The arguments a subcommand acts on when only its required positionals are given"
    args = {}
    for p in sub.positionals:
        args[p.name] = [] if p.multi else None
    for o in options(sub):
        args[o.key] = o.unset
    return args


def _value(name):
    return f"{name.upper()}_VALUE"


def required(sub):
    "Tokens and arguments for the subcommand's required positionals"
    tokens, args = [], {}
    for p in sub.positionals:
        if p.optional:
            continue
        if p.multi:
            vals = [f"{p.name}_1", f"{p.name}_2"]
            tokens += vals
            args[p.name] = vals
        else:
            tokens.append(f"{p.name}_value")
            args[p.name] = f"{p.name}_value"
    return tokens, args


def lines(sub):
    "Every generated (id, Line) for *sub*, then its table lines"
    req, req_args = required(sub)
    yield "defaults", Line(tuple(req), dict(req_args))

    optional = [p for p in sub.positionals if p.optional]
    if optional:
        toks = list(req) + [f"{p.name}_value" for p in optional]
        args = dict(req_args) | {p.name: f"{p.name}_value" for p in optional}
        yield "all-positionals", Line(tuple(toks), args)

    for o in options(sub):
        forms = []
        if o.flag:
            forms.append((o.long, (o.long,)))
            if o.short:
                forms.append((o.short, (o.short,)))
            value = True
        else:
            value = _value(o.key)
            forms.append((f"{o.long}=", (f"{o.long}={value}",)))
            forms.append((f"{o.long} ", (o.long, value)))
            if o.short:
                forms.append((f"{o.short} ", (o.short, value)))
        for label, toks in forms:
            yield label.strip(), Line(toks + tuple(req), dict(req_args) | {o.key: value})

    for i, line in enumerate(sub.lines):
        yield f"table{i}", line


def bad(command, sub):
    "Every generated (id, Bad) for *sub*, then its table's"
    req, _ = required(sub)
    yield "unknown-option", Bad(tuple(req) + ("--bogus-option",), ("--bogus-option",))

    for i, p in enumerate(sub.positionals):
        if p.optional:
            continue
        # drop this positional and every later one
        kept = []
        for q in sub.positionals[:i]:
            if q.optional:
                continue
            kept += [f"{q.name}_1", f"{q.name}_2"] if q.multi else [f"{q.name}_value"]
        yield f"missing-{p.name}", Bad(tuple(kept), (p.name,))

    for o in options(sub):
        if o.flag:
            continue
        yield f"no-value{o.long}", Bad(tuple(req) + (o.long,), (o.long,))
        if o.short:
            yield f"no-value{o.short}", Bad(tuple(req) + (o.short,), (o.short,))

    for i, b in enumerate(sub.bad):
        yield f"table{i}", b


def _subid(command, sub):
    return f"{command.prog}" + (f"-{sub.name}" if sub.name else "")


def subcommand_params():
    return [pytest.param(c, s, id=_subid(c, s)) for c in COMMANDS for s in c.subcommands]


def line_params():
    return [
        pytest.param(c, s, line, id=f"{_subid(c, s)}:{lid}")
        for c in COMMANDS
        for s in c.subcommands
        for lid, line in lines(s)
    ]


def bad_params():
    params = []
    for c in COMMANDS:
        for s in c.subcommands:
            for bid, b in bad(c, s):
                params.append(pytest.param(prefix(c, s) + b.argv, b, id=f"{_subid(c, s)}:{bid}"))
        if any(s.name for s in c.subcommands):
            b = Bad(("bogus-sub", "x"), ("bogus-sub",), "unknown subcommand")
            params.append(pytest.param((c.prog,) + b.argv, b, id=f"{c.prog}:unknown-subcommand"))
        for i, b in enumerate(c.bad):
            params.append(pytest.param((c.prog,) + b.argv, b, id=f"{c.prog}:table{i}"))
    return params
