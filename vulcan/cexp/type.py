
from dataclasses import dataclass
from typing import Any

class CExpr:
    pass


@dataclass
class Multigroup(CExpr):
    tag: str
    separator: str
    groups: list


@dataclass
class Group(CExpr):
    terms: list


class Term(CExpr):
    pass


@dataclass
class Const(Term):
    value: Any


@dataclass
class Name(Term):
    name: str


class Ident(Name):
    pass


class Operator(Name):
    pass
