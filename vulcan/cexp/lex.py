
import re

from dataclasses import dataclass
from typing import Any


@dataclass
class Token:
    type: str
    value: Any


pats = [
    ('space',     r'\s+'),
    ('comment',   r'//.*\n'),
    ('opar',      r'[({\[]'),
    ('cpar',      r'[)}\]]'),
    ('int',       r'-?[0-9]+'),
    ('op',        r'[!@$%^&*\-=+/?<>.:]+'),
    ('ident',     r'[_a-zA-Z][_a-zA-Z0-9]*'),
    ('bool',      r'#(?:true|false)'),
    ('undefined', r'#undefined'),
    ('string',    r'"[^"]+"'),
    ('separator', r'[,;]'),
    ('unknown',   r'.+?(?=\s)')
]

p = re.compile('|'.join(f'(?P<{g[0]}>{g[1]})' for g in pats))

def tokenize(buf):
    for tok_match in p.finditer(buf):
        tok_type = tok_match.lastgroup
        if tok_type != 'space' and tok_type != 'comment':
            tok_value = tok_match.group()
            match tok_type:
                case 'int':
                    tok_value = int(tok_value)
                case 'bool':
                    if tok_value == '#true':
                        tok_value = True
                    else:
                        tok_value = False
                case 'string':
                    tok_value = tok_value[1:-1]
                case 'opar' | 'cpar':
                    match tok_value:
                        case '(' | ')':
                            tok_value = 'parens'
                        case '{' | '}':
                            tok_value = 'braces'
                        case '[' | ']':
                            tok_value = 'brackets'
            yield(Token(tok_type, tok_value))
    while True:
        yield Token('eof', '')
