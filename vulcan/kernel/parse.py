
import vulcan.kernel.ast as ast
import vulcan.cexp.type as cexp


class ParseError(Exception):
    pass


def check_multigroup(stx, tag, separator):
    if not isinstance(stx, cexp.Multigroup):
        raise ParseError('expected multgroup, got %s', stx)

    if stx.tag != tag:
        raise ParseError('expected %s multgroup, got %s', tag, stx)

    if stx.separator != separator:
        if stx.separator and len(stx.groups) > 1:
            raise ParseError('expected separator %s, got %s', separator, stx.separator)


def parse_kernel(stx):
    # print(stx)
    if not isinstance(stx, cexp.Multigroup):
        raise ParseError("not a multigroup")
    if stx.tag != 'top' or stx.separator != False:
        raise ParseError("not a top multigroup")
    if len(stx.groups) != 1:
        raise ParseError("expected one group at top")
    return parse_expr(stx.groups[0])


def parse_expr(group):
    match len(group.terms):
        # const, ref
        case 1:
            return parse_at(group.terms)
        # app
        case 2:
            return parse_cp(group)
        # fun, let, fix, simple infix
        case 3:
            form = group.terms[0]
            if form == cexp.Ident("fun"):
                return parse_at(group)
            return parse_cp(group)
        # if, direct fun app
        case 4:
            return parse_cp(group)
        # more complex infix
        case _:
            return parse_cp(group)


def parse_at(terms):
    # XXX: ParseError for not an atom
    match len(terms):
        case 1:
            term = terms[0]
            if isinstance(term, cexp.Const):
                return ast.Datum(term.value)
            if isinstance(term, cexp.Ident):
                return ast.Ref(term.name)
            raise ParseError("expected const or ident, got %s", term)


def parse_cp(group):
    match len(group.terms):
        case 2:
            return parse_app(group)
        # let, fix, simple infix
        case 3:
            form = group.terms[0]
            if form == cexp.Ident("let"):
                return parse_let(group)
            if form == cexp.Ident("fix"):
                return parse_fix(group)
            return parse_infix(group.terms)
        # if
        case 4:
            form = group.terms[0]
            if form == cexp.Ident("if"):
                return parse_if(group)
            raise ParseError('cp: writeme')


def parse_app(group):
    terms = group.terms
    rator_stx = terms[0]
    rands_stx = terms[1]

    rator_ast = parse_at([rator_stx])
    check_multigroup(rands_stx, 'parens', ',')
    rands_ast = []
    for g in rands_stx.groups:
        rands_ast.append(parse_at(g.terms))
    return ast.App(rator_ast, rands_ast)

def parse_if(group):
    terms = group.terms
    test_stx = terms[1]
    then_stx = terms[2]
    else_stx = terms[3]

    test_ast = parse_at([test_stx])
    then_ast = parse_body(then_stx)
    else_ast = parse_body(else_stx)
    return ast.If(test_ast, then_ast, else_ast)


def parse_fix(group):
    binds = group.terms[1]
    body = group.terms[2]
    check_multigroup(binds, 'brackets', False)

    # XXX: empty binds should not make a Fix node
    binds = binds.groups[0].terms
    i = 0
    lbinds = len(binds)
    binds_ast = []

    while i < lbinds:
        if not binds[i] == cexp.Ident('fun'):
            raise ParseError("expected fun, got %s", binds[i])
        if i + 4 > lbinds:
            raise ParseError("not enough terms left, %s", binds[i:])
        b_name = binds[i+1].name
        b_args = binds[i+2]
        b_body = binds[i+3]
        fun = parse_fun(b_args, b_body)
        binds_ast.append((b_name, fun))
        i += 4

    body_ast = parse_body(body)
    return ast.Fix(binds_ast, body_ast)


def parse_let(group):
    binds = group.terms[1]
    body = group.terms[2]
    # XXX: empty binds should not make a Let node
    valid_binds_multigroup = (isinstance(binds, cexp.Multigroup) and
                              binds.tag == 'brackets' and
                              (binds.separator == ';' or
                               (not binds.separator and len(binds.groups) == 1)))
    if not valid_binds_multigroup:
        raise ParseError("expected var bindings, got %s", binds)

    binds_ast = []
    for g in binds.groups:
        terms = g.terms
        if len(terms) < 3:
            raise ParseError("expected var binding, got %s", terms)
        if not isinstance(terms[0], cexp.Ident):
            raise ParseError("expected ident, got %s", terms[0])
        name = terms[0].name
        if terms[1] != cexp.Operator('='):
            raise ParseError("expected '=', got %s", terms[1])
        # XXX: maybe not synth a Group here
        expr = parse_expr(cexp.Group(terms[2:]))
        binds_ast.append((name, expr))

    # print(binds_ast)

    body_ast = parse_body(body)
    return ast.Let(binds_ast, body_ast)


def parse_fun(args_stx, body_stx):
    valid_args_mg = (isinstance(args_stx, cexp.Multigroup) and
                     args_stx.tag == 'parens' and
                     (args_stx.separator == ',' or
                      (not args_stx.separator and (len(args_stx.groups) in (0, 1)))))
    if not valid_args_mg:
        raise ParseError("expected args, got %s", args_stx)

    args = []
    for g in args_stx.groups:
        vg = g.terms
        if len(vg) != 1:
            raise ParseError("expected one identifier, got %s", vg)
        if not isinstance(vg[0], cexp.Ident):
            raise ParseError("expected one identifier, got %s", vg[0])
        args.append(vg[0].name)

    valid_body_mg = (isinstance(body_stx, cexp.Multigroup) and
                     body_stx.tag == 'braces' and
                     body_stx.separator == ';' or
                     (not body_stx.separator and len(body_stx.groups) == 1))
    if not valid_body_mg:
        raise ParseError("expected body, got %s", body_stx)

    body_exprs = parse_body(body_stx)

    return ast.Fun(args, body_exprs)
    raise ParseError('fun: writeme')


def parse_body(body_stx):
    check_multigroup(body_stx, 'braces', ';')
    body_exprs = []
    for g in body_stx.groups:
        body_exprs.append(parse_expr(g))

    match len(body_exprs):
        case 0:
            raise ParseError("expected statments, got: %s body_stx")
        case 1:
            return body_exprs[0]
        case _:
            return ast.Seq(body_exprs)
    raise 'body: writeme'


def parse_infix(terms):
    match len(terms):
        case 3:
            if not isinstance(terms[1], cexp.Operator):
                raise ParseError("expected operator, got %s", terms[1])
            a = parse_at(terms[0:1])
            b = parse_at(terms[2:3])
            op = ast.Ref(terms[1].name)
            return ast.App(op, [a, b])
