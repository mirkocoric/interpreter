from __future__ import print_function
from __future__ import division
from collections import namedtuple
import os.path
import gc
import math
import logging
from itertools import chain
from random import randint
from inspect import getargspec
from workspace import WS

Var = namedtuple('Var', 'name value')
Command = namedtuple('Command', 'name args')
Procedure = namedtuple('Procedure', 'body args vars')

TEST_VAR = ":TEST"
logging.basicConfig(filename='example.log', level=logging.DEBUG)


class LogoCommands(object):
    def create_proc(self, line):
        par_line = line.split()
        if len(par_line) == 1:
            print ("NOT ENOUGH INPUTS TO TO")
            return
        elif getattr(self, str(par_line[1]), None):
            print("%s IS A PRIMITIVE" % par_line[1])
            return
        elif str(par_line[1]) in WS.proc:
            print("%s IS ALREADY DEFINED" % par_line[1])
            return
        for ind in xrange(2, len(par_line)):
            arg = par_line[ind]
            if not arg.startswith(":"):
                try:
                    print_argument_error("TO", arg)
                except ValueError:
                    pass
            else:
                par_line[ind] = arg[1:]

        body = []

        while(True):
            user_input = raw_input()
            if user_input == "END":
                WS.proc[par_line[1]] = Procedure(body, par_line[2:], {})
                print ("%s DEFINED" % par_line[1])
                return
            else:
                body.append(user_input)

    def exec_proc(self, proc):
        for line in proc.body:
            result = self.execute(proc, line)
            if result:
                return result

    def execute(self, proc, line):
        logging.debug(line)
        try:
            parsed_line = self.parse_line(proc, line)
        except ValueError:
            return
        arg_stack = []
        for parsed_item in reversed(parsed_line):
            if getattr(self, str(parsed_item), None):
                func = getattr(self, parsed_item, None)
                args = []
                min_args, opt_args = n_args((getargspec(func)))
                try:
                    for arg in xrange(min_args):
                        args.append(arg_stack.pop())
                except IndexError:
                    print("NOT ENOUGH INPUTS TO %s" % parsed_item)
                    return
                try:
                    for arg in xrange(opt_args):
                        args.append(arg_stack.pop())
                except IndexError:
                    pass
                try:
                    result = func(proc, *args)
                    if str(parsed_item) == "OUTPUT":
                        return result
                    elif result is not None:
                        arg_stack.append(result)
                except ValueError:
                    return
            elif isinstance(parsed_item, str):
                if parsed_item in WS.proc:
                    proc = WS.proc[parsed_item]
                    try:
                        for arg in proc.args:
                            proc.vars[arg] = arg_stack.pop()
                    except IndexError:
                        print("NOT ENOUGH INPUTS TO %s" % parsed_item)
                        return
                    result = self.exec_proc(proc)
                    if result is not None:
                        arg_stack.append(result)
                elif parsed_item.startswith("\""):
                    arg_stack.append(parsed_item[1:])
                else:
                    try:
                        print_undefined(parsed_item)
                    except ValueError:
                        return
            else:
                arg_stack.append(parsed_item)
        if arg_stack:
            try:
                print_parse_error(arg_stack[0])
            except ValueError:
                pass

    def parse_line(self, proc, line):
        """Returns parsed line"""
        if not isinstance(line, list):
            line = parse_space_list(line)
        args = connect_operators(line)
        if (not getattr(self, args[0], None) and
                args[0] not in WS.proc):
            print_undefined(args[0])
        parsed_args = [parse_args(arg) for arg in args]
        return [calc_expr(proc, arg) for arg in parsed_args]

    def LOAD(self, proc, f_name):
        if not os.path.isfile(f_name):
            print_undefined(f_name)
            return
        with open(f_name, 'r') as f:
            search_file(f)

    def SAVE(self, proc, f_name):
        if os.path.exists(f_name):
            print("FILE ALREADY EXISTS")
            return
        with open(f_name, 'w') as f:
            save_in_file(f)

    def LOCAL(self, proc, var):
        if proc:
            print (var)
            proc.vars[var] = None
        else:
            print("CAN ONLY DO THAT IN A PROCEDURE")
            raise ValueError

    def OUTPUT(self, proc, value):
        if proc:
            return value
        else:
            print("CAN ONLY DO THAT IN A PROCEDURE")
            raise ValueError

    def MAKE(self, proc, name, value):
        WS.vars.update({name: value})

    def NAME(self, proc, value, name):
        WS.vars.update({name: value})

    def PONS(self, proc):
        for var in WS.vars:
            print_variable(var)

    def POALL(self, proc):
        for proc in WS.proc:
            print_procedure(proc, WS.proc[proc])
        for var in WS.vars:
            print_variable(var)

    def PO(self, proc, name):
        if str(name) in WS.proc:
            print_procedure(name, WS.proc[str(name)])
        else:
            print ("%s IS UNDEFINED" % name)

    def DEFINEDP(self, proc, name):
        if str(name) in WS.proc:
            return True
        return False

    def READLIST(self, proc):
        return raw_input().split()

    def READWORD(self, proc):
        return raw_input().split()[0]

    def INT(self, proc, value):
        if is_float(value):
            return int(value)
        print_argument_error("INT", value)

    def PR(self, proc, value):
        if isinstance(value, list):
            for item in value:
                print (item, end=" ")
            print()
        else:
            print (value)

    def RECYCLE(self, proc):
        gc.collect()

    def ERALL(self, proc):
        WS.vars.clear()
        WS.proc.clear()

    def ERASE(self, proc, name):
        try:
            del WS.proc[name]
        except KeyError:
            print_undefined(name)

    def ERN(self, proc, name):
        if not isinstance(name, str):
            print_argument_error("ERN", name)
        try:
            del WS.vars[name]
        except KeyError:
            print_undefined(name)

    def ERNS(self, proc):
        WS.vars.clear()

    def ERPS(self, proc):
        WS.proc.clear()

    def ERASEFILE(self, proc, name):
        if not os.path.isfile(name):
            print_undefined(name)
            return
        try:
            os.remove(name)
        except:
            print("CANNOT ERASE THE FILE")

    def CATALOG(self, proc, name):
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        for f in files:
            print (f)

    def ASCII(self, proc, arg1):
        if isinstance(arg1, list):
            print_argument_error("ASCII", arg1)
        else:
            return ord(str(arg1)[0])

    def CHAR(self, proc, arg1):
        if not is_float(arg1):
            print_argument_error("CHAR", arg1)
        else:
            return chr(int(arg1))

    def COUNT(self, proc, arg1):
        if not isinstance(arg1, list):
            print_argument_error("COUNT", arg1)
        else:
            return len(arg1)

    def EMPTYP(self, proc, arg1):
        if arg1:
            return False
        return True

    def EQUALP(self, proc, arg1, arg2):
        if arg1 == arg2:
            return True
        return False

    def LISTP(self, proc, arg1):
        if isinstance(arg1, list):
            return True
        return False

    def MEMBERP(self, proc, arg1, arg2):
        if not isinstance(arg2, list):
            print_argument_error("MEMBERP", arg2)
        for item in arg2:
            if arg1 == item:
                return True
        return False

    def WORDP(self, proc, arg1):
        return not getattr(self, "LISTP", None)(proc, arg1)

    def NUMBERP(self, proc, arg1):
        if is_float(arg1):
            return True
        return False

    def NAMEP(self, proc, arg1):
        if arg1 in WS.vars:
            return True
        return False

    def THING(self, proc, arg1):
        if arg1 in WS.vars:
            return WS.vars[arg1]
        print ("%s HAS NO VALUE" % arg1)

    def OR(self, proc, arg1, arg2):
        if arg1 or arg2:
            return True
        return False

    def AND(self, proc, arg1, arg2):
        if arg1 and arg2:
            return True
        return False

    def PRODUCT(self, proc, arg1, arg2):
        if not is_float(arg1):
            print_argument_error("PRODUCT", arg1)
        elif not is_float(arg2):
            print_argument_error("PRODUCT", arg2)
        elif is_int(arg1) and is_int(arg2):
            return int(arg1) * int(arg2)
        else:
            return float(arg1) * float(arg2)

    def SUM(self, proc, arg1, arg2):
        if not is_float(arg1):
            print_argument_error("SUM", arg1)
        elif not is_float(arg2):
            print_argument_error("SUM", arg2)
        elif is_int(arg1) and is_int(arg2):
            return int(arg1) + int(arg2)
        else:
            return float(arg1) + float(arg2)

    def QUOTIENT(self, proc, arg1, arg2):
        if not is_float(arg1):
            print_argument_error("QUOTIENT", arg1)
        elif not is_float(arg2):
            print_argument_error("QUOTIENT", arg2)
        elif is_int(arg1) and is_int(arg2):
            if int(arg2) == 0:
                print("CAN'T DIVIDE BY ZERO")
                raise ValueError
            return int(arg1) / int(arg2)
        else:
            return float(arg1) / float(arg2)

    def ARCTAN(self, proc, arg1):
        if not is_float(arg1):
            print_argument_error("ARCTAN", arg1)
        else:
            return math.atan(float(arg1)) * 180 / math.pi

    def COS(self, proc, arg1):
        if not is_float(arg1):
            print_argument_error("COS", arg1)
        else:
            return math.cos(float(arg1) * math.pi / 180)

    def SIN(self, proc, arg1):
        if not is_float(arg1):
            print_argument_error("SIN", arg1)
        else:
            return math.sin(float(arg1) * math.pi / 180)

    def SQRT(self, proc, arg1):
        if not is_float(arg1):
            print_argument_error("SQRT", arg1)
        elif float(arg1) < 0:
            print_argument_error("SQRT", arg1)
        else:
            return math.sqrt(float(arg1))

    def REMAINDER(self, proc, arg1, arg2):
        if not is_int(arg1):
            print_argument_error("REMAINDER", arg1)
        elif not is_int(arg2):
            print_argument_error("REMAINDER", arg2)
        else:
            return int(arg1) % int(arg2)

    def RANDOM(self, proc, arg1):
        if not is_int(arg1):
            print_argument_error("RANDOM", arg1)
        else:
            return randint(0, int(arg1) - 1)

    def LIST(self, proc, arg1, arg2=None):
        var = [arg1]
        if arg2:
            var.append(arg2)
        return var

    def SE(self, proc, arg1, arg2=None):
        if isinstance(arg1, list):
            var = arg1
        else:
            var = [arg1]
        if isinstance(arg2, list):
            for item in arg2:
                var.append(item)
        elif arg2:
            var.append(arg2)
        return var

    def SENTENCE(self, proc, arg1, arg2=None):
        return getattr(self, "SE", None)(proc, arg1, arg2)

    def WORD(self, proc, arg1, arg2=None):
        if isinstance(arg1, list):
            print_argument_error("WORD", arg1)
        elif isinstance(arg2, list):
            print_argument_error("WORD", arg2)
        elif arg2:
            return str(arg1) + str(arg2)
        else:
            return str(arg1)

    def LPUT(self, proc, arg1, arg2):
        if not isinstance(arg2, list):
            print_argument_error("LPUT", arg2)
        arg2 = arg2 + [arg1]
        return arg2

    def FPUT(self, proc, arg1, arg2):
        if not isinstance(arg2, list):
            print_argument_error("FPUT", arg2)
        arg2 = [arg1] + arg2
        return arg2

    def FIRST(self, proc, arg1):
        if not arg1:
            print_argument_error("FIRST", arg1)
        if not isinstance(arg1, list):
            return str(arg1)[0]
        return arg1[0]

    def LAST(self, proc, arg1):
        if not arg1:
            print_argument_error("LAST", arg1)
        if not isinstance(arg1, list):
            return str(arg1)[-1]
        return arg1[-1]

    def BUTFIRST(self, proc, arg1):
        if not arg1:
            print_argument_error("BUTFIRST", arg1)
        if not isinstance(arg1, list):
            return str(arg1)[1:]
        return arg1[1:]

    def BF(self, proc, arg1):
        return getattr(self, "BUTFIRST", None)(proc, arg1)

    def BUTLAST(self, proc, arg1):
        if not arg1:
            print_argument_error("BUTLAST", arg1)
        if not isinstance(arg1, list):
            return str(arg1)[:-1]
        return arg1[:-1]

    def BL(self, proc, arg1):
        return getattr(self, "BUTLAST", None)(proc, arg1)

    def ITEM(self, proc, item, lst):
        if not isinstance(lst, list):
            print_argument_error("ITEM", lst)
        if not is_int(item):
            print_argument_error("ITEM", item)
        num = int(item)
        if num < 1:
            print_argument_error("ITEM", item)
        elif num > len(lst):
            print("TOO FEW ITEMS IN %s" % lst)
            raise ValueError
        else:
            return lst[num - 1]

    def IF(self, proc, pred, arg1, arg2=None):
        pred = check_pred(pred)
        if not isinstance(arg1, list):
            print_argument_error("IF", arg1)
        if not(isinstance(arg1, list) or not arg2):
            print_argument_error("IF", arg2)
        if pred:
            if arg1:
                self.execute(proc, arg1)
        elif arg2:
            self.execute(proc, arg2)

    def TEST(self, proc, pred):
        pred = check_pred(pred)
        if proc:
            proc.vars[TEST_VAR] = pred
        else:
            WS.vars[TEST_VAR] = pred

    def IFTRUE(self, proc, lst):
        if proc:
            if TEST_VAR in proc.vars:
                if proc.vars[TEST_VAR]:
                    self.execute(proc, lst)
        elif TEST_VAR in WS.vars:
            if WS.vars[TEST_VAR]:
                self.execute(proc, lst)

    def IFFALSE(self, proc, lst):
        if proc:
            if TEST_VAR in proc.vars:
                if not proc.vars[TEST_VAR]:
                    self.execute(proc, lst)
        elif TEST_VAR in WS.vars:
            if not WS.vars[TEST_VAR]:
                self.execute(proc, lst)


CMDS = LogoCommands()


def print_argument_error(func, item):
    print("%s DOESN'T LIKE %s AS INPUT" % (func, item))
    raise ValueError


def print_parse_error(item):
    print ("I DON'T KNOW WHAT TO DO WITH %s"
           % item)
    raise ValueError


def print_undefined(item):
    print ("I DON'T KNOW HOW TO %s" % item)
    raise ValueError


def print_variable(var):
    if isinstance(var, list):
        print ("%s IS [", end=" ")
        for item in var:
            print (item, end=" ")
        print("]")
    else:
        print ("%s IS %s" % (var, WS.vars[var]))


def print_procedure(name, proc):
    print ("TO %s" % name, end=" ")
    for arg in proc.args:
        print (":%s" % arg, end=" ")
    print()
    for line in proc.body:
        print (line)
    print ("END")
    print()


def is_int(name):
    """Returns True if the string is int"""
    try:
        float_name = float(name)
        int_name = int(float_name)
        if int_name == float_name:
            return True
        return False
    except:
        return False


def is_float(name):
    """Returns True if it is possible to convert string to float"""
    try:
        float(name)
        return True
    except:
        return False


def check_pred(pred):
    if pred == "TRUE":
        return True
    elif pred == "FALSE":
        return False
    elif not isinstance(pred, bool):
        print("%s IS NOT TRUE OR FALSE" % pred)
        raise ValueError
    return pred


def connect_operators(line):
    parsed_line = [line[0]]
    for ind in xrange(len(line) - 1):
        if not line[ind + 1] or not line[ind]:
            parsed_line.append(line[ind + 1])
        elif is_operator(line[ind][-1]) or is_operator(line[ind + 1][0]):
            parsed_line[-1] += line[ind + 1]
        else:
            parsed_line.append(line[ind + 1])
    return parsed_line


def parse_space_list(line):
    args = []
    line = (ch for ch in line)
    operand = ""
    for ch in line:
        if ch == "[":
            args.append(parse_list(line))
        elif ch == " ":
            if operand:
                args.append(operand)
                operand = ""
        else:
            operand += ch
    if operand:
        args.append(operand)
    return args


def convert(op):
    if is_int(op):
        return int(op)
    elif is_float(op):
        return float(op)
    return op


def parse_list(expr):
    lst = []
    op = ""
    for ch in expr:
        if ch == "]":
            if op:
                lst.append(convert(op))
            return lst
        elif ch == "[":
            lst.append(parse_list(expr))
        elif ch == " ":
            if op:
                lst.append(convert(op))
            op = ""
        else:
            op += ch
    return lst


def check_valid(expr):
    valid = True
    if len(expr) == 1:
        if (is_plus_minus(expr[-1]) or is_em_prod_div(expr[-1])):
            valid = False
    elif (is_plus_minus(expr[-1]) or is_em_prod_div(expr[-1]) and
            is_plus_minus(expr[-2]) or is_em_prod_div(expr[-2])):
        valid = False
    if not valid:
        print("NOT ENOUGH INPUTS TO %s" % expr[-1])
        raise ValueError


def calc_expr(proc, expr):
    operators = []
    operands = []
    ret_expr = []
    last_num = False
    negative = False
    if isinstance(expr[0], list):
        return expr[0]
    check_valid(expr)
    expr = (item for item in expr)
    for item in expr:
        if item == ")":
            while True:
                try:
                    operator = operators.pop()
                except:
                    print_parse_error(")")
                    raise ValueError('PARSE ERROR')
                if operator == "(":
                    break
                operands.append(perform_operation(operands, operator))
            last_num = True
        elif is_plus_minus(item) and not last_num:
            if item == "-":
                operands.append(0)
                try:
                    op = parse(proc, expr.next())
                except StopIteration:
                    print("NOT ENOUGH INPUTS TO -")
                    raise ValueError
                operands.append(op)
                operands.append(perform_operation(operands, item))
                last_num = True
        elif (is_plus_minus(item) and
              is_em_prod_div(operators)):
            while operators:
                operands.append(perform_operation(operands, operators.pop()))
            operators.append(item)
            last_num = False
        elif is_operator(item):
            operators.append(item)
            last_num = False
        else:
            result = parse(proc, item)
            if result is not None:
                operands.append(result)
                last_num = True
            else:
                operands.append(item)
                last_num = False
    while operators:
        operands.append(perform_operation(operands, operators.pop()))
    return operands.pop()


def parse_str(item):
    if str(item).startswith("\""):
        return str(item)[1:]
    else:
        return item


def parse(proc, item):
    if is_int(item):
        return int(item)
    elif is_float(item):
        return float(item)
    elif item.startswith(":"):
        if proc:
            if item[1:] in proc.vars:
                return proc.vars.get(item[1:])
        elif item[1:] in WS.vars:
            return WS.vars.get(item[1:])
        else:
            print ("%s HAS NO VALUE" % item[1:])
            raise ValueError('VARIABLE DOESNT EXIST')


def perform_operation(operands, operator):
    try:
        operand2 = operands.pop()
    except IndexError:
        print("NOT ENOUGH INPUTS TO %s" % operator)
        raise ValueError
    try:
        operand1 = operands.pop()
    except IndexError:
        return operand2
    if not is_float(operand1):
        print_argument_error(operator, operand1)
    if not is_float(operand2):
        print_argument_error(operator, operand2)
    if operator == "+":
        return operand1 + operand2
    if operator == "-":
        return operand1 - operand2
    if operator == "*":
        return operand1 * operand2
    if operator == "/":
        return float(operand1) / operand2
    if operator == "=":
        return operand1 == operand2


def is_operator(ch):
    operators = "()-+*/=[]"
    for operator in operators:
        if ch == operator:
            return True
    return False


def is_plus_minus(ch):
    operators = "-+"
    for operator in operators:
        if ch == operator:
            return True
    return False


def is_em_prod_div(operators):
    if not operators:
        return True
    prod_div = "*/"
    for operator in prod_div:
        if operators[- 1:][0] == operator:
            return True
    return False


def parse_args(arg):
    if not isinstance(arg, str):
        return [arg]
    operand = ""
    l = []
    for ch in arg:
        if is_operator(ch):
            if operand:
                l.append(operand)
                operand = ""
            l.append(ch)
        else:
            operand += ch
    if operand:
        l.append(operand)
    return l


def n_args(func_args):
    args = len(func_args.args) - 2
    opt_args = 0
    if func_args.defaults:
        opt_args = len(func_args.defaults)
    min_args = args - opt_args
    return min_args, opt_args


def search_file(f):
    in_procedure = False
    while(True):
        line = f.readline()
        if not line:
            return
        words = line.split()
        if not in_procedure and words[0] != "TO":
            WS.vars.update({words[0]: "".join(words[1:])})
        elif line.strip() == "END":
            WS.proc[name] = Procedure(body, args, {})
            in_procedure = False
        elif in_procedure:
            body.append(line[:-1])
        else:
            name = words[1]
            args = words[2:]
            body = []
            in_procedure = True


def save_in_file(f):
    for name in WS.proc:
        proc = WS.proc[name]
        f.write("TO %s " % name)
        for arg in proc.args:
            f.write("%s " % arg)
        f.write("\n")
        for line in proc.body:
            f.write("%s \n" % line)
        f.write("END\n")
    for var in WS.vars:
        f.write("%s %s \n" % (var, WS.vars[var]))
