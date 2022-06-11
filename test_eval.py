
from unittest import TestCase

import ast, read
from eval import Interpreter


class TestInterpreter(TestCase):
    def setUp(self):
        from eval import Interpreter
        self.intp = Interpreter()

    def to_ast(self, s):
        a_sexp = read.read_all(s)
        return ast.sexp_to_ast_seq(a_sexp)

    def test_basic(self):
        an_ast = self.to_ast('(#%let ([x (#%datum 42)])\n  x)')
        self.assertEqual(self.intp.eval(an_ast), 42)

    def test_plus(self):
        an_ast = self.to_ast('''
          (#%let ([x (#%datum 3)]
                  [y (#%datum 4)])
            (#%primapp plus x y))''')
        self.assertEqual(self.intp.eval(an_ast), 7)

    def test_letrec_factorial(self):
        an_ast = self.to_ast('''
          (#%letrec ([factorial
                       (#%lambda (x)
                         (#%if (#%primapp is_zero x)
                               (#%datum 1)
                               (#%primapp mult x
                                          (#%app factorial
                                            (#%primapp sub1 x)))))])
           (#%app factorial (#%datum 10)))
        ''')
        self.assertEqual(self.intp.eval(an_ast), 3628800)
