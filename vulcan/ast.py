

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


class LetrecExpr(Expr):
    def __init__(self, b_vars, b_exprs, body):
        self.b_vars = b_vars
        self.b_exprs = b_exprs
        self.body = body


class SeqExpr(Expr):
    def __init__(self, exprs):
        self.exprs = exprs


class SetExpr(Expr):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr


class RefExpr(Expr):
    def __init__(self, name):
        self.name = name


class DatumExpr(Expr):
    def __init__(self, a_value):
        self.value = a_value


class IfExpr(Expr):
    def __init__(self, test, conseq, alter):
        self.test = test
        self.conseq = conseq
        self.alter = alter


class LambdaExpr(Expr):
    def __init__(self, args, body):
        self.args = args
        self.body = body


class AppExpr(Expr):
    def __init__(self, rator, rands):
        self.rator = rator
        self.rands = rands


class PrimAppExpr(Expr):
    def __init__(self, name, rands):
        self.name = name
        self.rands = rands


def letform_sexp_to_ast(let_expr_cls, a_sexp):
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
    return let_expr_cls(b_vars, b_exprs, body_ast)


def sexp_to_ast(a_sexp):
    if isinstance(a_sexp, list):
        tag = a_sexp[0]
        if tag == '#%primapp':
            rator = a_sexp[1]
            rands = sexps_to_ast(a_sexp[2:])
            if not isinstance(rator, str):
                raise Exception('operator should be an identifier for primapp got: {!r}'.format(bv))
            return PrimAppExpr(rator, rands)
        elif tag == '#%app':
            rator = sexp_to_ast(a_sexp[1])
            rands = sexps_to_ast(a_sexp[2:])
            return AppExpr(rator, rands)
        elif tag == '#%lambda':
            args = a_sexp[1]
            body = sexp_to_ast_seq(a_sexp[2:])
            return LambdaExpr(args, body)
        elif tag == '#%if':
            test = sexp_to_ast(a_sexp[1])
            conseq = sexp_to_ast(a_sexp[2])
            alter = sexp_to_ast(a_sexp[3])
            return IfExpr(test, conseq, alter)
        elif tag == '#%let':
            return letform_sexp_to_ast(LetExpr, a_sexp)
        elif tag == '#%letrec':
            return letform_sexp_to_ast(LetrecExpr, a_sexp)
        elif tag == '#%set!':
            name = a_sexp[1]
            if not isinstance(name, str):
                raise Exception('name should be an identifier got: {!r}'.format(bv))
            return SetExpr(a_sexp[1], sexp_to_ast(a_sexp[2]))
        elif tag == '#%datum':
            return DatumExpr(a_sexp[1])
    elif isinstance(a_sexp, str):
        return RefExpr(a_sexp)
    raise Exception('cannot parse {!r}'.format(a_sexp))


def sexps_to_ast(a_list):
    return [sexp_to_ast(e) for e in a_list]


def sexp_to_ast_seq(a_list):
    if len(a_list) == 1:
        return sexp_to_ast(a_list[0])
    else:
        return SeqExpr(sexps_to_ast(a_list))


if __name__ == '__main__':
    import read
    seq = read.read_all('(#%let ([x (#%datum 42)])\n  x)')
    print(sexp_to_ast_seq(seq))

