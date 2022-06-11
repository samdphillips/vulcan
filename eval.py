
from prim import Primitives


class EmptyEnv:
    def extend(self, vars, vals):
        return Env(self, vars, vals)

    def get(self, name):
        raise Exception(f'{name} is not defined')


class Env:
    def __init__(self, parent, vars, vals):
        self.parent = parent
        self.binds = dict(zip(vars,vals))

    def get(self, name):
        if name in self.binds:
            return self.binds[name]
        else:
            return self.parent.get(name)


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


class KLet:
    def __init__(self, env, bind_vals, an_ast):
        self.env = env
        self.bind_vals = bind_vals
        self.ast = an_ast

    def step(self, intp, a_value):
        b_vals = self.bind_vals + [a_value]
        if len(self.ast.b_vars) == len(b_vals):
            intp.extend_env(self.ast.b_vars, b_vals)
            intp.doing(self.ast.body)
        else:
            i = len(b_vals)
            intp.push_k(KLet(self.env, b_vals, self.ast))
            intp.doing(self.ast.b_exprs[i])


class KPrim:
    def __init__(self, env, an_ast, vals):
        self.env = env
        self.ast = an_ast
        self.vals = vals

    def step(self, intp, val):
        vals = self.vals + [val]
        if len(self.ast.rands) == len(vals):
            intp.do_primitive(self.ast.name, vals)
        else:
            i = len(vals)
            intp.push_k(KPrim(self.env, self.ast, vals))
            intp.doing(self.ast.rands[i])


class Doing:
    def __init__(self, an_ast):
        self.ast = an_ast

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

    def doing(self, an_ast):
        self.state = Doing(an_ast)

    def done(self, a_value):
        self.state = Done(a_value)

    def push_k(self, k):
        self.stack.push(k)

    def extend_env(self, vars, vals):
        self.env = self.env.extend(vars, vals)

    def eval(self, an_ast):
        self.state = Doing(an_ast)
        self.halt = False
        return self.run()

    def run(self):
        while not self.halt:
            self.step()
        return self.state.value

    def step(self):
        self.state.step(self)

    def do_primitive(self, name, args):
        prim = getattr(self, f'prim_{name}')
        self.done(prim(*args))

    def visit(self, an_ast):
        return an_ast.visit(self)

    def ret(self, a_value):
        frame = self.stack.pop()
        self.env = frame.env
        frame.step(self, a_value)

    def visit_let(self, a_let):
        self.push_k(KLet(self.env, [], a_let))
        self.doing(a_let.b_exprs[0])

    def visit_datum(self, a_datum):
        self.done(a_datum.value)

    def visit_ref(self, a_ref):
        self.done(self.env.get(a_ref.name))

    def visit_primapp(self, a_primapp):
        self.push_k(KPrim(self.env, a_primapp, []))
        self.doing(a_primapp.rands[0])


if __name__ == '__main__':
    import ast, read
    a_sexp = read.read_all('(#%let ([x (#%datum 42)])\n  x)')
    an_ast = ast.sexp_to_ast_seq(a_sexp)
    i = Interpreter()
    print(i.eval(an_ast))


