
from vulcan.cexp.read import read_all
from vulcan.kernel.parse import parse_kernel
from vulcan.kernel.interp import kernel_eval

def eval_check(expected):
    def inner(f):
        src = f()
        a_cexp = read_all(src)
        an_ast = parse_kernel(a_cexp)
        result = kernel_eval(an_ast)
        assert result == expected
    return inner

@eval_check(42)
def test_basic_datum():
    return "42"

@eval_check(7)
def test_basic_add():
    return "3 + 4"
