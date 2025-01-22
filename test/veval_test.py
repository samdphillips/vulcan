
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

@eval_check(3628800)
def test_recurse_factorial():
    return """
fix [fun factorial (n0) {
       let [z = n0 == 1] {
         if z {
           1
         } {
           let [n1 = n0 - 1] {
             let [r1 = factorial(n1)] { n0 * r1 }
           }
         }
      }
    }] {
  factorial(10)
}
    """

odd_even_recurse = """
fix [fun is_odd(n) {
       let [no = n == 1] {
         if no {
           no
         } {
           let [nz = n == 0] {
             if nz {
               false
             } {
               let [n1 = n - 1] { is_even(n1) }
             }
           }
         }
       }
     }
     fun is_even(n) {
       let [nz = n == 0] {
         if nz {
           nz
         } {
           let [no = n == 1] {
             if no {
               false
             } {
               let [n1 = n - 1] { is_odd(n1) }
             }
           }
         }
       }
     }] {
  %s
}
"""

@eval_check(True)
def test_odd1():
    return odd_even_recurse % "is_odd(1)"

@eval_check(True)
def test_even2():
    return odd_even_recurse % "is_even(2)"

@eval_check(False)
def test_even3():
    return odd_even_recurse % "is_even(3)"


@eval_check(True)
def test_even10():
    return odd_even_recurse % "is_even(10)"
