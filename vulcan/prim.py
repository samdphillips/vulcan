# pylint: disable=invalid-name

from .type import Box, undefined


class Primitives:
    def prim_box(self, value):
        return Box(value)

    def prim_set_box(self, box, value):
        box.value = value
        return None

    def prim_unbox(self, box):
        if box.value is undefined:
            raise Error('undefined variable accessed')
        return box.value

    def prim_is_zero(self, a):
        return a == 0

    def prim_is_equal(self, a, b):
        return a == b

    def prim_plus(self, a, b):
        return a + b

    def prim_mult(self, a, b):
        return a * b

    def prim_add1(self, a):
        return a + 1

    def prim_sub1(self, a):
        return a - 1
