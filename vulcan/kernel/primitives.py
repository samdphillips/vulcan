
all_primitives = []

class Primitive:
    def __init__(self, names, proc):
        self.names = names
        self.proc = proc

    def apply(self, intp, args):
        # XXX: error checking
        # XXX: calling protocols
        intp.done(self.proc(*args))


def primitive(*n):
    def inner(proc):
        names = list(n) + [proc.__name__]
        p = Primitive(names, proc)
        all_primitives.append(p)
        return p
    return inner


@primitive("+")
def add(a, b):
    return a + b
