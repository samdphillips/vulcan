
from dataclasses import dataclass
from typing import Any


class Expr:
    def visit(self, visitor, *args, **kwargs):
        base_name = self.__class__.__name__.lower()
        name = f'visit_{base_name}'
        method = getattr(visitor, name)
        return method(self, *args, **kwargs)


class Let(Expr):
    def __init__(self, b_vars, b_exprs, body):
        self.b_vars = b_vars
        self.b_exprs = b_exprs
        self.body = body


class Seq(Expr):
    def __init__(self, exprs):
        self.exprs = exprs


@dataclass
class Ref(Expr):
    name: str

    def atomic_eval(self, intp):
        # XXX: better error handling
        return intp.env.lookup(self.name, None, lambda k,v: v)


@dataclass
class Datum(Expr):
    value: Any

    def atomic_eval(self, intp):
        return self.value


class If(Expr):
    def __init__(self, test, conseq, alter):
        self.test = test
        self.conseq = conseq
        self.alter = alter


class Fun(Expr):
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def atomic_eval(self, intp):
        return intp.make_closure(self)


@dataclass
class App(Expr):
    rator: Expr
    rands: list
