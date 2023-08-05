
from unittest import TestCase

from vulcan.ast import sexp_to_ast_seq
from vulcan.eval import Interpreter
from vulcan.read import read_all


class TestInterpreter(TestCase):
    def setUp(self):
        self.intp = Interpreter()

    def to_ast(self, a_string):
        a_sexp = read_all(a_string)
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
          (#%let ([factorial (#%primapp box (#%datum #undefined))])
            (#%primapp set_box
                       factorial
                       (#%lambda (x)
                         (#%if (#%primapp is_zero x)
                               (#%datum 1)
                               (#%primapp mult x
                                          (#%app (#%primapp unbox factorial)
                                            (#%primapp sub1 x))))))
            (#%app (#%primapp unbox factorial) (#%datum 10)))
        ''')
        self.assertEqual(self.intp.eval(an_ast), 3628800)

    def test_odd_even(self):
        pgm = '''
          (#%let ([= (#%lambda (a b) (#%primapp is_equal a b))]
                  [odd? (#%primapp box (#%datum #undefined))]
                  [even? (#%primapp box (#%datum #undefined))])
            (#%primapp set_box
                       odd?
                       (#%lambda (n)
                         (#%let ([z (#%app = n (#%datum 1))])
                           (#%if z
                             z
                             (#%if (#%primapp is_zero n)
                               (#%datum #f)
                               (#%app (#%primapp unbox even?) (#%primapp sub1 n)))))))
            (#%primapp set_box
                       even?
                       (#%lambda (n)
                         (#%let ([z (#%primapp is_zero n)])
                           (#%if z
                             z
                             (#%if (#%app = n (#%datum 1))
                               (#%datum #f)
                               (#%app (#%primapp unbox odd?) (#%primapp sub1 n)))))))
            (#%app (#%primapp unbox {}) (#%datum {})))
        '''
        ast0 = self.to_ast(pgm.format('odd?', 10))
        self.assertEqual(self.intp.eval(ast0), False)

        ast1 = self.to_ast(pgm.format('odd?', 11))
        self.assertEqual(self.intp.eval(ast1), True)

        ast2 = self.to_ast(pgm.format('even?', 11))
        self.assertEqual(self.intp.eval(ast2), False)

        ast3 = self.to_ast(pgm.format('even?', 10))
        self.assertEqual(self.intp.eval(ast3), True)


    def test_mut_counter(self):
        pgm = '''
          (#%let ([c (#%primapp box (#%datum 0))])
            (#%let ([incr! (#%lambda () (#%primapp set_box c (#%primapp add1 (#%primapp unbox c))))])
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%primapp unbox c)))
        '''
        ast = self.to_ast(pgm)
        self.assertEqual(self.intp.eval(ast), 5)

