
from .lex import Token, tokenize
from .type import *

# cexpr := group [ sep group ]* sep?
# group := term *
# term  := '(' cexpr ')'
#        | '[' cexpr ']'
#        | '{' cexpr '}'
#        | <ident>
#        | <op>
#        | datum
# datum := <int> | <string> | <bool>


class Peek:
    def __init__(self, base):
        self.base = base
        self.cur = None

    def peek(self):
        if not self.cur:
            self.cur = next(self.base)
        return self.cur

    def __next__(self):
        if self.cur:
            ret = self.cur
            self.cur = None
        else:
            ret = next(self.base)
        return ret


class MultigroupBuilder:
    def __init__(self):
        self.separator = False

    def is_separator(self, tok):
        if tok == self.separator:
            return True
        elif tok.type == 'separator' and not self.separator:
            self.separator = tok
            return True
        else:
            return False

    def build(self, groups):
        sep = self.separator and self.separator.value
        return Multigroup(self.tag, sep, groups)


class TopBuilder(MultigroupBuilder):
    tag = 'top'

    def is_close_group(self, tok):
        return tok == Token('eof', '')


class NestedBuilder(MultigroupBuilder):
    def __init__(self, tag):
        super().__init__()
        self.tag = tag
        self.closer = Token('cpar', tag)

    def is_close_group(self, tok):
        return tok == self.closer


def read_term(toks):
    tok = next(toks)
    match tok.type:
        case 'opar':
            return read_multigroup(toks, NestedBuilder(tok.value))
        case 'ident':
            return Ident(tok.value)
        case 'op':
            return Operator(tok.value)
        case 'int' | 'string' | 'bool':
            return Const(tok.value)
    raise Exception('expected term, got: %s', tok)


def read_group(toks, shape):
    terms = []
    while True:
        tok = toks.peek()
        if shape.is_close_group(tok):
            return Group(terms)
        elif shape.is_separator(tok):
            next(toks)
            return Group(terms)
        elif tok.type == 'cpar':
            raise Exception('wrong closer, got: %s', tok)
        # XXX: "wrong" separator error
        terms.append(read_term(toks))


def read_multigroup(toks, shape):
    groups = []
    while True:
        tok = toks.peek()
        if shape.is_close_group(tok):
            next(toks)
            return shape.build(groups)
        elif tok.type == 'cpar':
            raise Exception('wrong closer, got: %s', tok)
        groups.append(read_group(toks, shape))


def read_all(s):
   toks = Peek(tokenize(s))
   return read_multigroup(toks, TopBuilder())
