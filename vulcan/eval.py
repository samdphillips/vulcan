
from .prim import Primitives
from .type import Closure


class EmptyEnv:
    def extend(self, vars, vals):
        return Env(self, vars, vals)

    def get(self, name):
        raise Exception(f'{name} is not defined')

    def set(self, name, val):
        raise Exception(f'{name} is not defined')

class Env(EmptyEnv):
    def __init__(self, parent, vars, vals):
        self.parent = parent
        self.binds = dict(zip(vars,vals))

    def get(self, name):
        if name in self.binds:
            return self.binds[name]
        else:
            return self.parent.get(name)

    def set(self, name, val):
        if name in self.binds:
            self.binds[name] = val
        else:
            self.parent.set(name, val)


class Stack:
    def __init__(self):
        self.frames = []

    def push(self, frame):
        self.frames = [frame] + self.frames

    def pop(self):
        top = self.frames[0]
        self.frames = self.frames[1:]
        return top


class KHalt:
    env = EmptyEnv()

    def step(self, intp, v):
        intp.halt = True


class KIf:
    def __init__(self, env, ast):
        self.env = env
        self.ast = ast

    def step(self, intp, val):
        res = val is not False
        intp.env = self.env
        if res:
            intp.doing(self.ast.conseq)
        else:
            intp.doing(self.ast.alter)


class KSet:
    def __init__(self, env, ast):
        self.env = env
        self.ast = ast

    def step(self, intp, val):
        intp.env = self.env
        intp.env.set(self.ast.name, val)
        intp.done(None)


class KLet:
    def __init__(self, env, bind_vals, ast):
        self.env = env
        self.bind_vals = bind_vals
        self.ast = ast

    def step(self, intp, a_value):
        b_vals = self.bind_vals + [a_value]
        if len(self.ast.b_vars) == len(b_vals):
            intp.extend_env(self.ast.b_vars, b_vals)
            intp.doing(self.ast.body)
        else:
            i = len(b_vals)
            intp.push_k(KLet(self.env, b_vals, self.ast))
            intp.doing(self.ast.b_exprs[i])


class KLetrec:
    def __init__(self, env, bind_vals, ast):
        self.env = env
        self.bind_vals = bind_vals
        self.ast = ast

    def step(self, intp, a_value):
        b_vals = self.bind_vals + [a_value]
        if len(self.ast.b_vars) == len(b_vals):
            for var, val in zip(self.ast.b_vars, b_vals):
                self.env.set(var, val)
            intp.env = self.env
            intp.doing(self.ast.body)
        else:
            i = len(b_vals)
            intp.push_k(KLetrec(self.env, b_vals, self.ast))
            intp.doing(self.ast.b_exprs[i])


class KSeq:
    def __init__(self, env, ast, i):
        self.env = env
        self.ast = ast
        self.i = i

    def step(self, intp, a_value):
        intp.env = self.env
        intp.doing(self.ast.exprs[self.i])
        next_i = self.i + 1
        if next_i < len(self.ast.exprs):
            intp.push_k(KSeq(self.env, self.ast, next_i))


class KPrim:
    def __init__(self, env, ast, vals):
        self.env = env
        self.ast = ast
        self.vals = vals

    def step(self, intp, val):
        vals = self.vals + [val]
        if len(self.ast.rands) == len(vals):
            intp.do_primitive(self.ast.name, vals)
        else:
            i = len(vals)
            intp.push_k(KPrim(self.env, self.ast, vals))
            intp.doing(self.ast.rands[i])


class KRator:
    def __init__(self, env, ast):
        self.env = env
        self.ast = ast

    def step(self, intp, val):
        if len(self.ast.rands) == 0:
            intp.apply_procedure(val, [])
        else:
            intp.push_k(KRands(self.env, self.ast, val, []))
            intp.doing(self.ast.rands[0])


class KRands:
    def __init__(self, env, ast, rator, vals):
        self.env = env
        self.ast = ast
        self.rator = rator
        self.vals = vals

    def step(self, intp, val):
        vals = self.vals + [val]
        if len(self.ast.rands) == len(vals):
            intp.apply_procedure(self.rator, vals)
        else:
            i = len(vals)
            intp.push_k(KRands(self.env, self.ast, self.rator, vals))
            intp.doing(self.ast.rands[i])


class Doing:
    def __init__(self, ast):
        self.ast = ast

    def step(self, intp):
        intp.visit(self.ast)


class Done:
    def __init__(self, a_value):
        self.value = a_value

    def step(self, intp):
        intp.ret(self.value)


class Interpreter(Primitives):
    def __init__(self):
        self.halt = True
        self.state = None
        self.stack = Stack()
        self.stack.push(KHalt())
        self.env = EmptyEnv()

    def doing(self, ast):
        assert ast is not None
        self.state = Doing(ast)

    def done(self, a_value):
        self.state = Done(a_value)

    def push_k(self, k):
        self.stack.push(k)

    def extend_env(self, vars, vals):
        self.env = self.env.extend(vars, vals)

    def eval(self, ast):
        self.stack = Stack()
        self.push_k(KHalt())
        self.state = Doing(ast)
        self.halt = False
        return self.run()

    def run(self):
        while not self.halt:
            self.step()
        return self.state.value

    def step(self):
        self.state.step(self)

    def apply_procedure(self, proc, args):
        proc.apply(self, args)

    def do_primitive(self, name, args):
        prim = getattr(self, f'prim_{name}')
        self.done(prim(*args))

    def visit(self, ast):
        return ast.visit(self)

    def ret(self, a_value):
        frame = self.stack.pop()
        self.env = frame.env
        frame.step(self, a_value)

    def visit_let(self, a_let):
        self.push_k(KLet(self.env, [], a_let))
        self.doing(a_let.b_exprs[0])

    def visit_letrec(self, a_letrec):
        count = len(a_letrec.b_vars)
        self.extend_env(a_letrec.b_vars, [None] * count)
        self.push_k(KLetrec(self.env, [], a_letrec))
        self.doing(a_letrec.b_exprs[0])

    def visit_lambda(self, a_lambda):
        self.done(Closure(self.env, a_lambda))

    def visit_datum(self, a_datum):
        self.done(a_datum.value)

    def visit_ref(self, a_ref):
        self.done(self.env.get(a_ref.name))

    def visit_set(self, a_set):
        self.push_k(KSet(self.env, a_set))
        self.doing(a_set.expr)

    def visit_seq(self, a_seq):
        if len(a_seq.exprs) > 1:
            self.push_k(KSeq(self.env, a_seq, 1))
        self.doing(a_seq.exprs[0])

    def visit_if(self, an_if):
        self.push_k(KIf(self.env, an_if))
        self.doing(an_if.test)

    def visit_primapp(self, a_primapp):
        self.push_k(KPrim(self.env, a_primapp, []))
        self.doing(a_primapp.rands[0])

    def visit_app(self, an_app):
        self.push_k(KRator(self.env, an_app))
        self.doing(an_app.rator)


if __name__ == '__main__':
    import ast, read
    a_sexp = read.read_all('(#%let ([x (#%datum 42)])\n  x)')
    an_ast = ast.sexp_to_ast_seq(a_sexp)
    i = Interpreter()
    print(i.eval(an_ast))


