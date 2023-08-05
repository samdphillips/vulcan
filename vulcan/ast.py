

class Expr:
    def visit(self, visitor, *args, **kwargs):
        base_name = self.__class__.__name__[:-4].lower()
        name = f'visit_{base_name}'
        method = getattr(visitor, name)
        return method(self, *args, **kwargs)


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


def let_sexp_to_ast(a_sexp):
    bindings = a_sexp[1]
    body = a_sexp[2:]
    bind_vars = []
    bind_exprs = []
    for bind_var, bind_expr in bindings:
        if not isinstance(bind_var, str):
            raise Exception(f'binding should be a symbol got: {bind_var!r}')
        bind_vars.append(bind_var)
        bind_exprs.append(sexp_to_ast(bind_expr))
    body_ast = sexp_to_ast_seq(body)
    return LetExpr(bind_vars, bind_exprs, body_ast)


def sexp_to_ast(a_sexp):
    if isinstance(a_sexp, list):
        tag = a_sexp[0]
        if tag == '#%prim':
            rator = a_sexp[1]
            rands = sexps_to_ast(a_sexp[2:])
            if not isinstance(rator, str):
                raise Exception(f'operator should be an identifier for primapp got: {rator!r}')
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
            return let_sexp_to_ast(a_sexp)
        elif tag == '#%begin':
            return sexp_to_ast_seq(a_sexp[1:])
        elif tag == '#%datum':
            return DatumExpr(a_sexp[1])
    elif isinstance(a_sexp, str):
        return RefExpr(a_sexp)
    raise Exception(f'cannot parse {a_sexp!r}')


def sexps_to_ast(a_list):
    return [sexp_to_ast(e) for e in a_list]


def sexp_to_ast_seq(a_list):
    if len(a_list) == 1:
        return sexp_to_ast(a_list[0])
    else:
        return SeqExpr(sexps_to_ast(a_list))
