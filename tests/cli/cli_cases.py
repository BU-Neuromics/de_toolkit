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
    "The subcommand's own options and the common options it takes"
    return sub.options + tuple(o for o in COMMON if o.long not in sub.without_common)


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


def given(o, value):
    "The argument an option given once with *value* yields: a list for a repeat option"
    return [value] if o.repeat else value


def required_parts(sub, skip=None):
    """
    Tokens and arguments for the subcommand's required options (but *skip*)
    and positionals: (the tokens before ``--``, the ``--`` and the words
    after it, or () when the subcommand takes nothing after ``--``, args)
    """
    before, after, args = [], [], {}
    for o in sub.options:
        if o.required and o is not skip:
            value = _value(o.key)
            before += [o.long, value]
            args[o.key] = given(o, value)
    for p in sub.positionals:
        if p.optional:
            continue
        if p.multi:
            vals = [f"{p.name}_1", f"{p.name}_2"]
        else:
            vals = [f"{p.name}_value"]
        (after if p.after_dashdash else before).extend(vals)
        args[p.name] = vals if p.multi else vals[0]
    if after:
        after = ["--"] + after
    return tuple(before), tuple(after), args


def required(sub, skip=None):
    "Tokens and arguments for the subcommand's required options and positionals"
    before, after, args = required_parts(sub, skip)
    return before + after, args


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
            # an option with choices takes one of them; a BOOL takes True,
            # which the parser hands the command as a bool (DETK-0081)
            token = o.choices[0] if o.choices else _value(o.key)
            value = token
            if o.metavar == "BOOL":
                token, value = "True", True
            forms.append((f"{o.long}=", (f"{o.long}={token}",)))
            forms.append((f"{o.long} ", (o.long, token)))
            if o.short:
                forms.append((f"{o.short} ", (o.short, token)))
        # a required option given in one of its forms is not given again
        o_req, o_args = required(sub, skip=o) if o.required else (req, req_args)
        for label, toks in forms:
            yield label.strip(), Line(toks + tuple(o_req), dict(o_args) | {o.key: given(o, value)})

    for i, line in enumerate(sub.lines):
        yield f"table{i}", line


def bad(command, sub):
    "Every generated (id, Bad) for *sub*, then its table's"
    # an argument added to a command line goes before its "--", if any
    before, after, _ = required_parts(sub)
    yield "unknown-option", Bad(before + ("--bogus-option",) + after, ("--bogus-option",))

    opts = []
    for o in sub.options:
        if o.required:
            opts += [o.long, _value(o.key)]
    for i, p in enumerate(sub.positionals):
        if p.optional:
            continue
        # drop this positional and every later one
        kept = list(opts)
        for q in sub.positionals[:i]:
            if q.optional or q.after_dashdash:
                continue
            kept += [f"{q.name}_1", f"{q.name}_2"] if q.multi else [f"{q.name}_value"]
        yield f"missing-{p.name}", Bad(tuple(kept), (p.name,))

    for o in sub.options:
        if o.required:
            b, a, _ = required_parts(sub, skip=o)
            yield f"missing{o.long}", Bad(b + a, (o.long,))

    for o in options(sub):
        if o.flag:
            continue
        yield f"no-value{o.long}", Bad(before + (o.long,) + after, (o.long,))
        if o.short:
            yield f"no-value{o.short}", Bad(before + (o.short,) + after, (o.short,))

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
