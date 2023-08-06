

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

    def atomic_eval(self, intp):
        return intp.env.get(self.name)


class DatumExpr(Expr):
    def __init__(self, a_value):
        self.value = a_value

    def atomic_eval(self, intp):
        return self.value


class IfExpr(Expr):
    def __init__(self, test, conseq, alter):
        self.test = test
        self.conseq = conseq
        self.alter = alter


class LambdaExpr(Expr):
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def atomic_eval(self, intp):
        return intp.make_closure(self)

class AppExpr(Expr):
    def __init__(self, rator, rands):
        self.rator = rator
        self.rands = rands


class PrimAppExpr(Expr):
    def __init__(self, name, rands):
        self.name = name
        self.rands = rands


def classify_sexp(a_sexp):
    if isinstance(a_sexp, list):
        tag = a_sexp[0]
        if tag in ('#%datum', '#%lambda'):
            return 'aexp'
        elif tag in ('#%prim', '#%app', '#%if'):
            return 'cexp'
        elif tag in ('#%let', '#%begin'):
            return 'exp'
    elif isinstance(a_sexp, str):
        return "aexp"
    raise Exception(f'cannot classify {a_sexp!r}')


def parse_sexp_exp(a_sexp):
    a_sexp_t = classify_sexp(a_sexp)
    if a_sexp_t == 'aexp':
        return parse_sexp_aexp(a_sexp)
    elif a_sexp_t == 'cexp':
        return parse_sexp_cexp(a_sexp)
    elif a_sexp_t == 'exp':
        tag = a_sexp[0]
        if tag == '#%let':
            return parse_let_sexp(a_sexp)
        elif tag == '#%begin':
            return parse_sexp_seq(a_sexp[1:])
    raise Exception(f'cannot handle exp {a_sexp!r}')


def parse_let_sexp(a_sexp):
    bindings = a_sexp[1]
    body = a_sexp[2:]
    if body == []:
        raise Exception(f'#%let with empty body {a_sexp!r}')
    bind_vars = []
    bind_exprs = []
    for bind_var, bind_expr in bindings:
        if not isinstance(bind_var, str):
            raise Exception(f'binding should be a symbol got: {bind_var!r}')
        bind_vars.append(bind_var)
        bind_exprs.append(parse_sexp_exp(bind_expr))
    body_ast = parse_sexp_seq(body)
    return LetExpr(bind_vars, bind_exprs, body_ast)


def parse_sexp_aexp(a_sexp):
    a_sexp_t = classify_sexp(a_sexp)
    if a_sexp_t != 'aexp':
        raise Exception(f'expected aexp got {a_sexp_t}')

    if isinstance(a_sexp, list):
        tag = a_sexp[0]
        if tag == '#%lambda':
            # XXX: check that these are symbols
            args = a_sexp[1]
            body = parse_sexp_seq(a_sexp[2:])
            return LambdaExpr(args, body)
        elif tag == '#%datum':
            return DatumExpr(a_sexp[1])
    elif isinstance(a_sexp, str):
        return RefExpr(a_sexp)
    raise Exception(f'cannot handle aexp {a_sexp!r}')


def parse_sexp_cexp(a_sexp):
    a_sexp_t = classify_sexp(a_sexp)
    if a_sexp_t != 'cexp':
        raise Exception(f'expected cexp got {a_sexp_t}')

    if isinstance(a_sexp, list):
        tag = a_sexp[0]
        if tag == '#%prim':
            # XXX : check that this is a symbol
            rator = a_sexp[1]
            rands = parse_sexps(parse_sexp_aexp, a_sexp[2:])
            if not isinstance(rator, str):
                raise Exception(f'operator should be an identifier for primapp got: {rator!r}')
            return PrimAppExpr(rator, rands)
        elif tag == '#%app':
            rator = parse_sexp_aexp(a_sexp[1])
            rands = parse_sexps(parse_sexp_aexp, a_sexp[2:])
            return AppExpr(rator, rands)
        elif tag == '#%if':
            test = parse_sexp_aexp(a_sexp[1])
            conseq = parse_sexp_exp(a_sexp[2])
            alter = parse_sexp_exp(a_sexp[3])
            return IfExpr(test, conseq, alter)
    raise Exception(f'cannot handle cexp {a_sexp!r}')


def parse_sexps(parse, a_list):
    return [parse(e) for e in a_list]


def parse_sexp_seq(a_list):
    if len(a_list) == 1:
        return parse_sexp_exp(a_list[0])
    else:
        return SeqExpr(parse_sexps(parse_sexp_exp, a_list))
