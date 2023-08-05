
import re

pats = [
  ('space',     r'\s+'),
  ('opar',      r'[({\[]'),
  ('cpar',      r'[)}\]]'),
  ('ident',     r'(?:#%)?[!@$%^&*=+_/?<>a-zA-Z-][!@$%^&*=+_/?<>a-zA-Z0-9-.]*'),
  ('int',       r'[0-9]+'),
  ('bool',      r'#(?:t(?:rue)?|f(?:alse)?)'),
  ('undefined', r'#undefined'),
  ('unknown',   r'.')
]

p = re.compile('|'.join(f'(?P<{g[0]}>{g[1]})' for g in pats))

def tokenize(buf):
    for match in p.finditer(buf):
        tok_type = match.lastgroup
        if tok_type != 'space':
            yield(tok_type, match.group())
