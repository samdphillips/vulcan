
import re

pats = [
  ('space',   r'\s+'),
  ('opar',    r'[({\[]'),
  ('cpar',    r'[)}\]]'),
  ('ident',   r'(?:#%)?[!@$%^&*=+_/?<>a-zA-Z-][!@$%^&*=+_/?<>a-zA-Z0-9-]*'),
  ('int',     r'[0-9]+'),
  ('unknown', r'.')
]

p = re.compile('|'.join('(?P<{}>{})'.format(*g) for g in pats))

def tokenize(buf):
    for m in p.finditer(buf):
        type = m.lastgroup
        if type != 'space':
            yield(type, m.group())

if __name__ == '__main__':
    buf = '(let ([x 42])\n  x)'
    for x in tokenize(buf):
        print(x)

