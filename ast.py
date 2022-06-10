

class Expr:
    def visit(self, visitor, *args, **kwargs):
        base_name = self.__class__.__name__[:-4].lower()
        name = f'visit_{base_name}'
        m = getattr(visitor, name)
        return m(self, *args, **kwargs)


class LetExpr(Expr):
    def __init__(self, b_vars, b_exprs, body):
        self.b_vars = b_vars
        self.b_exprs = b_exprs
        self.body = body


class SeqExpr(Expr):
    def __init__(self, exprs):
        self.exprs = exprs


class RefExpr(Expr):
    def __init__(self, name):
        self.name = name


class DatumExpr(Expr):
    def __init__(self, a_value):
        self.value = a_value


def let_sexp_to_ast(a_sexp):
    bindings = a_sexp[1]
    body = a_sexp[2:]
    b_vars = []
    b_exprs = []
    for bv, be in bindings:
        if not isinstance(bv, str):
            raise Exception('binding should be a symbol got: {!r}'.format(bv))
        b_vars.append(bv)
        b_exprs.append(sexp_to_ast(be))
    body_ast = sexp_to_ast_seq(body)
    return LetExpr(b_vars, b_exprs, body_ast)

def sexp_to_ast(a_sexp):
    if isinstance(a_sexp, list):
        tag = a_sexp[0]
        if tag == '#%let':
            return let_sexp_to_ast(a_sexp)
        elif tag == '#%datum':
            return DatumExpr(a_sexp[1])
    elif isinstance(a_sexp, str):
        return RefExpr(a_sexp)
    raise Exception('cannot parse {!r}'.format(a_sexp))


def sexp_to_ast_seq(a_list):
    if len(a_list) == 1:
        return sexp_to_ast(a_list[0])
    else:
        asts = [sexp_to_ast(e) for e in a_list]
        return SeqExpr(asts)


if __name__ == '__main__':
    import read
    seq = read.read_all('(#%let ([x (#%datum 42)])\n  x)')
    print(sexp_to_ast_seq(seq))

