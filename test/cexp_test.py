
import pytest

from vulcan.cexp.read import read_all, read_term
from vulcan.cexp.lex import Token, tokenize

def tokenize_eof(s):
    toks = tokenize(s)
    def get_token():
        return next(toks)
    return iter(get_token, Token('eof', ''))

class TestCexpLex:
    def test_literals(self):
        toks = [tok for tok in tokenize_eof('42 -33 #true #false')]
        assert [tok.type for tok in toks] == ['int', 'int', 'bool', 'bool']
        assert [tok.value for tok in toks] == [42, -33, True, False]

    def test_operators(self):
        toks = [tok for tok in tokenize_eof('+ = += ++ -')]
        assert [tok.type for tok in toks] == ['op', 'op', 'op', 'op', 'op']
        assert [tok.value for tok in toks] == ['+', '=', '+=', '++', '-']

    def test_comments(self):
        toks = [tok for tok in tokenize_eof('42 // this is a test \n 43')]
        assert [tok.type for tok in toks] == ['int', 'int']
        assert [tok.value for tok in toks] == [42, 43]

    def test_expression(self):
        toks = [tok for tok in tokenize_eof('stdout.println(stuff, mode)')]
        assert ([tok.type for tok in toks]
                  == ['ident', 'op', 'ident', 'opar', 'ident', 'separator',
                      'ident', 'cpar'])
        assert ([tok.value for tok in toks]
                  == ['stdout', '.', 'println', 'parens', 'stuff',
                      ',', 'mode', 'parens'])

    def test_string(self):
        toks = [tok for tok in tokenize_eof('  "this is a test"  ')]
        assert toks[0].type == 'string'
        assert toks[0].value == 'this is a test'

class TestCexpRead:
    def test_simple_term(self):
        p = read_term(tokenize('abc'))
        assert p.is_term

    def test_top1(self):
        p = read_all('123 + 456')
        assert p.tag == 'top'
        assert len(p.groups) == 1
        assert len(p.groups[0].terms) == 3

    def test_top2(self):
        p = read_all('3 + 4 * 2')
        assert p.tag == 'top'
        assert len(p.groups) == 1
        assert len(p.groups[0].terms) == 5

    def test_top3(self):
        p = read_all('3 + (4 * 2)')
        assert p.tag == 'top'
        assert len(p.groups) == 1
        assert len(p.groups[0].terms) == 3

    def test_top4(self):
        p = read_all('a[10,11]')
        g = p.groups[0].terms
        assert len(g) == 2
        assert g[1].tag == 'brackets'
        assert g[1].separator == ','
        assert len(g[1].groups) == 2

    def test_top5(self):
        read_all('fun factorial(n, acc) { if (n == 1) { acc } else { factorial(n - 1, n * acc) } }')

    def test_top_empty(self):
        read_all(';;;')
