
from unittest import TestCase

from vulcan.ast import parse_sexp_seq
from vulcan.eval import Interpreter
from vulcan.read import read_all


class TestInterpreter(TestCase):
    def setUp(self):
        self.intp = Interpreter()

    def to_ast(self, a_string):
        a_sexp = read_all(a_string)
        return parse_sexp_seq(a_sexp)

    def test_basic(self):
        an_ast = self.to_ast('(#%let ([x (#%datum 42)])\n  x)')
        self.assertEqual(self.intp.eval(an_ast), 42)

    def test_plus(self):
        an_ast = self.to_ast('''
          (#%let ([x (#%datum 3)]
                  [y (#%datum 4)])
            (#%prim plus x y))''')
        self.assertEqual(self.intp.eval(an_ast), 7)

    def test_recurse_factorial(self):
        an_ast = self.to_ast('''
          (#%let ([factorial-loc (#%prim box (#%datum #undefined))])
            (#%prim set_box
                       factorial-loc
                       (#%lambda (x)
                         (#%let ([is_zero-result (#%prim is_zero x)])
                           (#%if is_zero-result
                                 (#%datum 1)
                                 (#%let ([rec (#%prim unbox factorial-loc)]
                                         [x0  (#%prim sub1 x)])
                                   (#%let ([x1 (#%app rec x0)])
                                     (#%prim mult x x1)))))))
            (#%let ([factorial (#%prim unbox factorial-loc)])
              (#%app factorial (#%datum 10))))
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
                         (#%let ([even? (#%prim unbox even?)]
                                 [no (#%app = n (#%datum 1))])
                           (#%if no
                             no
                             (#%let ([nz (#%prim is_zero n)])
                               (#%if nz
                                 (#%datum #f)
                                 (#%let ([n-1 (#%prim sub1 n)])
                                   (#%app even? n-1))))))))
            (#%prim set_box
                       even?
                       (#%lambda (n)
                         (#%let ([odd? (#%prim unbox odd?)]
                                 [nz (#%prim is_zero n)])
                           (#%if nz
                             nz
                             (#%let ([no (#%app = n (#%datum 1))])
                               (#%if no
                                 (#%datum #f)
                                 (#%let ([n-1 (#%prim sub1 n)])
                                   (#%app odd? n-1))))))))
            (#%let ([f (#%prim unbox {})])
              (#%app f (#%datum {}))))
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
            (#%let ([incr! (#%lambda ()
                             (#%let ([v0 (#%prim unbox c)])
                               (#%let ([v1 (#%prim add1 v0)])
                                 (#%prim set_box c v1))))])
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%app incr!)
              (#%prim unbox c)))
        '''
        ast = self.to_ast(pgm)
        self.assertEqual(self.intp.eval(ast), 5)

