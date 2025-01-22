

class Undefined:
    pass

undefined = Undefined()


class Box:
    def __init__(self, value):
        self.value = value


class Closure:
    def __init__(self, env, ast):
        self.env = env
        self.ast = ast

    def apply(self, intp, vals):
        print(f"adding {self.ast.args} <= {vals}")
        env = intp.env
        for lhs,rhs in zip(self.ast.args, vals):
            env = env.insert(lhs, rhs)
        intp.env = env
        intp.doing(self.ast.body)
