
from unittest import TestCase

from vulcan.ast import sexp_to_ast_seq
from vulcan.eval import Interpreter
from vulcan.read import read_all


class TestInterpreter(TestCase):
    def setUp(self):
        from vulcan.eval import Interpreter
        self.intp = Interpreter()

    def to_ast(self, s):
        a_sexp = read_all(s)
        return sexp_to_ast_seq(a_sexp)

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

    def test_odd_even(self):
        pgm = '''
          (#%letrec ([= (#%lambda (a b) (#%primapp is_equal a b))]
                     [odd?
                       (#%lambda (n)
                         (#%let ([z (#%app = n (#%datum 1))])
                           (#%if z
                             z
                             (#%if (#%primapp is_zero n)
                               (#%datum #f)
                               (#%app even? (#%primapp sub1 n))))))]
                     [even?
                       (#%lambda (n)
                         (#%let ([z (#%primapp is_zero n)])
                           (#%if z
                             z
                             (#%if (#%app = n (#%datum 1))
                               (#%datum #f)
                               (#%app odd? (#%primapp sub1 n))))))])
            (#%app {} (#%datum {})))
        '''
        ast0 = self.to_ast(pgm.format('odd?', 10))
        self.assertEqual(self.intp.eval(ast0), False)

        ast1 = self.to_ast(pgm.format('odd?', 11))
        self.assertEqual(self.intp.eval(ast1), True)

