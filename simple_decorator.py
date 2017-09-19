def validate_args(types):
    def decorator(func):
        def check_args(*args, **kwargs):
            for arg, typ in zip(args[1:], types):
                if type(arg) not in typ:
                    raise ValueError("Wrong argument type")
            return func(*args, **kwargs)
        return check_args
    return decorator


class Interpreter(object):
    @validate_args(types=[[int, float], [int, float]])
    def multiply(self, arg1, arg2):
        return arg1 * arg2

    @validate_args(types=[[str], [str]])
    def append(self, arg1, arg2):
        return arg1 + arg2

it = Interpreter()
print it.multiply(2, 3)
try:
    print it.multiply(4, "A")
except ValueError as err:
    print err.message
print(it.append("A", "B"))
try:
    print(it.append(2, 3))
except ValueError as err:
    print(err.message)
