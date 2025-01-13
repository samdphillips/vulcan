
import vulcan.kernel.ast as ast
import vulcan.cexp.type as cexp


class ParseError(Exception):
    pass


def parse_kernel(stx):
    print(stx)
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

def parse_infix(terms):
    match len(terms):
        case 3:
            if not isinstance(terms[1], cexp.Operator):
                raise ParseError("expected operator, got %s", terms[1])
            a = parse_at(terms[0:1])
            b = parse_at(terms[2:3])
            op = ast.Ref(terms[1].name)
            return ast.App(op, [a, b])
