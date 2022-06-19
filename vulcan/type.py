

class Closure:
    def __init__(self, env, ast):
        self.env = env
        self.ast = ast

    def apply(self, intp, vals):
        intp.env = self.env.extend(self.ast.args, vals)
        intp.doing(self.ast.body)
