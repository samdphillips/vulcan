
from .lex import tokenize


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
    ty, val = next(toks)
    if ty == 'unknown':
        raise Exception(f'unknown token: {val!r}')
    elif ty == 'opar':
        return read_list(toks, val)
    elif ty == 'int':
        return int(val)
    elif ty == 'bool':
        return val[1] == 't'
    else:
        return val


closers = {'(': ')', '[': ']', '{': '}'}
def read_list(toks, opener):
    ret = []
    while True:
        try:
            ty, val = toks.peek()
            if ty == 'cpar':
                if val == closers[opener]:
                    next(toks)
                    return ret
                else:
                    raise Exception('unmatched closer, {!r} {!r}'.format(opener, val))
            ret.append(read_one(toks))
        except StopIteration:
            raise Exception('unclosed term, starts with {!r}'.format(ret[0]))


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
