
from .prim import Primitives
from .type import Closure


class EmptyEnv:
    # pylint: disable=redefined-builtin
    def extend(self, vars, vals):
        return Env(self, vars, vals)

    def get(self, name):
        raise Exception(f'{name} is not defined')


class Env(EmptyEnv):
    # pylint: disable=redefined-builtin
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

    # pylint: disable=unused-argument
    def step(self, intp, value):
        intp.halt = True


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


class KSeq:
    def __init__(self, env, ast, i):
        self.env = env
        self.ast = ast
        self.i = i

    # pylint: disable=unused-argument
    def step(self, intp, value):
        intp.env = self.env
        intp.doing(self.ast.exprs[self.i])
        next_i = self.i + 1
        if next_i < len(self.ast.exprs):
            intp.push_k(KSeq(self.env, self.ast, next_i))


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

    # pylint: disable=redefined-builtin
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

    def atomic_eval(self, ast):
        return ast.atomic_eval(self)

    def make_closure(self, a_lambda):
        return Closure(self.env, a_lambda)

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

    def visit_lambda(self, a_lambda):
        self.done(self.make_closure(a_lambda))

    def visit_datum(self, a_datum):
        self.done(a_datum.value)

    def visit_ref(self, a_ref):
        self.done(self.env.get(a_ref.name))

    def visit_seq(self, a_seq):
        if len(a_seq.exprs) > 1:
            self.push_k(KSeq(self.env, a_seq, 1))
        self.doing(a_seq.exprs[0])

    def visit_if(self, an_if):
        val = self.atomic_eval(an_if.test)
        if val is not False:
            self.doing(an_if.conseq)
        else:
            self.doing(an_if.alter)

    def visit_primapp(self, a_primapp):
        rands = [a.atomic_eval(self) for a in a_primapp.rands]
        self.do_primitive(a_primapp.name, rands)

    def visit_app(self, an_app):
        rator = an_app.rator.atomic_eval(self)
        rands = [a.atomic_eval(self) for a in an_app.rands]
        self.apply_procedure(rator, rands)
