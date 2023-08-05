
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
            (#%prim plus x y))''')
        self.assertEqual(self.intp.eval(an_ast), 7)

    def test_letrec_factorial(self):
        an_ast = self.to_ast('''
          (#%let ([factorial (#%prim box (#%datum #undefined))])
            (#%prim set_box
                       factorial
                       (#%lambda (x)
                         (#%if (#%prim is_zero x)
                               (#%datum 1)
                               (#%prim mult x
                                          (#%app (#%prim unbox factorial)
                                            (#%prim sub1 x))))))
            (#%app (#%prim unbox factorial) (#%datum 10)))
        ''')
        self.assertEqual(self.intp.eval(an_ast), 3628800)

    def test_odd_even(self):
        pgm = '''
          (#%let ([= (#%lambda (a b) (#%prim is_equal a b))]
                  [odd? (#%prim box (#%datum #undefined))]
                  [even? (#%prim box (#%datum #undefined))])
            (#%prim set_box
                       odd?
                       (#%lambda (n)
                         (#%let ([z (#%app = n (#%datum 1))])
                           (#%if z
                             z
                             (#%if (#%prim is_zero n)
                               (#%datum #f)
                               (#%app (#%prim unbox even?) (#%prim sub1 n)))))))
            (#%prim set_box
                       even?
                       (#%lambda (n)
                         (#%let ([z (#%prim is_zero n)])
                           (#%if z
                             z
                             (#%if (#%app = n (#%datum 1))
                               (#%datum #f)
                               (#%app (#%prim unbox odd?) (#%prim sub1 n)))))))
            (#%app (#%prim unbox {}) (#%datum {})))
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
          (#%let ([c (#%prim box (#%datum 0))])
            (#%let ([incr! (#%lambda () (#%prim set_box c (#%prim add1 (#%prim unbox c))))])
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%prim unbox c)))
        '''
        ast = self.to_ast(pgm)
        self.assertEqual(self.intp.eval(ast), 5)

