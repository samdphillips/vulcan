
from dataclasses import dataclass
from typing import Any


class Expr:
    def visit(self, visitor, *args, **kwargs):
        base_name = self.__class__.__name__.lower()
        name = f'visit_{base_name}'
        method = getattr(visitor, name)
        return method(self, *args, **kwargs)


@dataclass
class Let(Expr):
    binds: list
    body: Expr


@dataclass
class Fix(Expr):
    binds: list
    body: Expr


@dataclass
class Seq(Expr):
    exprs: list


@dataclass
class Ref(Expr):
    name: str

    def atomic_eval(self, intp):
        # XXX: better error handling
        return intp.do_ref(self)


@dataclass
class Datum(Expr):
    value: Any

    def atomic_eval(self, intp):
        return self.value


@dataclass
class If(Expr):
    test: Expr
    conseq : Expr
    alter: Expr

@dataclass
class Fun(Expr):
    args: list
    body: Expr

    def atomic_eval(self, intp):
        return intp.make_closure(self)


@dataclass
class App(Expr):
    rator: Expr
    rands: list
