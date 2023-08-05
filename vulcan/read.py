
from .lex import tokenize
from .type import undefined


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


def read_one(toks):
    tok_type, tok_value = next(toks)
    if tok_type == 'unknown':
        raise Exception(f'unknown token: {tok_value!r}')
    elif tok_type == 'opar':
        return read_list(toks, tok_value)
    elif tok_type == 'int':
        return int(tok_value)
    elif tok_type == 'bool':
        return tok_value[1] == 't'
    elif tok_type == 'undefined':
        return undefined
    else:
        return tok_value


closers = {'(': ')', '[': ']', '{': '}'}
def read_list(toks, opener):
    ret = []
    while True:
        try:
            tok_type, tok_value = toks.peek()
            if tok_type == 'cpar':
                if tok_value == closers[opener]:
                    next(toks)
                    return ret
                else:
                    raise Exception(f'unmatched closer, {opener!r} {tok_value!r}')
            ret.append(read_one(toks))
        except StopIteration:
            # pylint: disable=raise-missing-from
            raise Exception(f'unclosed term, starts with {ret[0]!r}')


def read_all(buf):
    toks = Peek(tokenize(buf))
    ret = []
    try:
        while True:
            ret.append(read_one(toks))
    except StopIteration:
        pass
    return ret


if __name__ == '__main__':
    print(read_all('(let ([x 42])\n  x)'))
    # read_all('(let')
