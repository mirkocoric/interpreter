class myDecorator(object):
    def Multiply(self, a, b):
        try:
            self.check_args(self, {a: [int, float], b: [int, float]})
        except ValueError as ve:
            return ve.message
        return a * b

    def Append(self, a, b):
        try:
            self.check_args(self, {a: [str], b: [str]})
        except ValueError as ve:
            return ve.message
        return a + b

    def check_args(self, func, args):
        for arg in args:
            found = False
            for arg_type in args[arg]:
                if type(arg) == arg_type:
                    found = True
            if not found:
                raise ValueError("Wrong argument type")
        return func


d = myDecorator()

print(d.Multiply(2, 3))
print(d.Multiply(4, "A"))
print(d.Append(2, 3))
print(d.Append("A", "B"))
