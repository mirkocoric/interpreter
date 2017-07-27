from collections import namedtuple
import os.path
import gc
import math
from inspect import getargspec
from workspace import WS


Var = namedtuple('Var', 'name value')
Command = namedtuple('Command', 'name args')
Procedure = namedtuple('Procedure', 'body args vars')


class LogoCommands(object):
    def exec_proc(self, command):
        proc = WS.proc.get(command.name)
        if not proc:
            return False
        for argc, argp in zip(command.args, proc.args):
            WS.vars.update({argp: argc})
        for line in proc.body:
            self.execute(proc, line)
        return True

    def execute(self, proc, line):
        parsed_line = self.parse_line(line)
        if not parsed_line:
            return
        arg_stack = []
        for parsed_item in reversed(parsed_line):
            if getattr(self, str(parsed_item), None):
                func = getattr(self, parsed_item, None)
                args = []
                min_args, opt_args = return_num_args((getargspec(func)))
                try:
                    for arg in xrange(min_args):
                        args.append(arg_stack.pop())
                except:
                    print("NOT ENOUGH INPUTS TO %s" % parsed_item)
                    return
                try:
                    for arg in xrange(opt_args):
                        args.append(arg_stack.pop())
                except:
                    pass
                result = func(proc, *args)
                if result:
                    arg_stack.append(result)
                elif result is False:
                    return
            elif isinstance(parsed_item, str):
                if parsed_item in WS.proc:
                    WS.proc[parsed_item]
                    # TODO
                    # self.exec_proc(command)
                else:
                    arg_stack.append(parsed_item)
            else:
                arg_stack.append(parsed_item)
        if arg_stack:
            print_parse_error(arg_stack[0])

    def parse_line(self, line):
        """Returns parsed line"""
        args = line.split(" ")
        if (not getattr(self, args[0], None) and
                args[0] not in WS.proc):
            print_undefined(args[0])
            return
        parsed_line = [args[0]]
        if len(args) == 1:
            return parsed_line
        for ind in xrange(len(args) - 1):
            if is_operator(args[ind][-1]) or is_operator(args[ind + 1][0]):
                parsed_line[-1] += args[ind + 1]
            else:
                parsed_line.append(args[ind + 1])
        try:
            parsed_line = [calc_expr(item) for item in parsed_line]
        except ValueError:
            return
        return parsed_line

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
            proc.vars.update({var, None})
        else:
            print "CAN ONLY DO THAT IN A PROCEDURE"

    def MAKE(self, proc, name, value):
        if value:
            WS.vars.update({name: value})

    def PON(self, proc, name):
        if WS.vars[name]:
            print "%s IS %s" % (name, WS.vars[name])
        else:
            print_undefined(name)

    def PONS(self, proc):
        for var in WS.vars:
            print "%s IS %s" % (var, WS.vars[var])

    def POALL(self, proc):
        for proc in WS.proc:
            print WS.proc[proc]
        for var in WS.vars:
            print "%s IS %s" % (var, WS.vars[var])

    def PO(self, proc, name):
        if WS.proc[name]:
            print WS.proc[name]
        else:
            print_undefined(name)

    def INT(self, proc, value):
        if is_float(value):
            return int(value)
        print "INT DOESN'T LIKE %s AS INPUT"

    def PR(self, proc, value):
        if isinstance(value, list):
            print(str(value)[1:-1])
        else:
            print value

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
        if name.startswith(":"):
            try:
                del WS.vars[name[1:]]
            except KeyError:
                print_undefined(name[1:])
        else:
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
            print f

    def PRODUCT(self, proc, arg1, arg2):
        return arg1 * arg2

    def LIST(self, proc, arg1, arg2=None):
        var = [arg1]
        if arg2:
            var.append(arg2)
        return var

    def LPUT(self, proc, arg1, arg2):
        if not isinstance(arg2, list):
            print("LPUT DOESN'T LIKE %s AS INPUT" % arg2)
            return False
        arg2 = arg2 + [arg1]
        return arg2

    def FPUT(self, proc, arg1, arg2):
        if not isinstance(arg2, list):
            print("LPUT DOESN'T LIKE %s AS INPUT" % arg2)
            return False
        arg2 = [arg1] + arg2
        return arg2

    def FIRST(self, proc, arg1):
        if not isinstance(arg1, list) or not arg1:
            print("FIRST DOESN'T LIKE %s AS INPUT" % arg1)
            return False
        return arg1[0]

    def LAST(self, proc, arg1):
        if not isinstance(arg1, list) or not arg1:
            print("LAST DOESN'T LIKE %s AS INPUT" % arg1)
            return False
        return arg1[-1]

    def BUTFIRST(self, proc, arg1):
        if not isinstance(arg1, list) or not arg1:
            print("BUTFIRST DOESN'T LIKE %s AS INPUT" % arg1)
            return False
        if len(arg1) == 1:
            print_parse_error("[]")
            return False
        return arg1[1:]

    def BF(self, proc, arg1):
        return getattr(self, "BUTFIRST", None)(proc, arg1)

    def BUTLAST(self, proc, arg1):
        if not isinstance(arg1, list) or not arg1:
            print("BUTLAST DOESN'T LIKE %s AS INPUT" % arg1)
        if len(arg1) == 1:
            print_parse_error("[]")
            return False
        return arg1[:-1]

    def BL(self, proc, arg1):
        return getattr(self, "BUTLAST", None)(proc, arg1)

    def ITEM(self, proc, item, lst):
        if not is_int(item):
            print("ITEM DOESN'T LIKE %s AS INPUT" % item)
            return False
        num = int(item)
        if num < 1:
            print("ITEM DOESN'T LIKE %s AS INPUT" % item)
            return False
        elif num > len(lst):
            print("TOO FEW ITEMS IN %s" % lst)
            return False
        else:
            return lst[num - 1]


CMDS = LogoCommands()


def print_parse_error(item):
    print ("I DON'T KNOW WHAT TO DO WITH %s"
           % item)


def print_undefined(item):
    print "I DON'T KNOW HOW TO %s" % item


def is_int(name):
    """Returns True if the string is int"""
    try:
        float_name = float(name)
        int_name = int(float_name)
        if int_name == float_name:
            return True
        return False
    except ValueError:
        return False


def is_float(name):
    """Returns True if it is possible to convert string to float"""
    try:
        float(name)
        return True
    except ValueError:
        return False


def calc_expr(arg):
    expr = arg_to_list(arg)
    operators = []
    operands = []
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
        elif (is_plus_minus(item) and
              is_em_prod_div(operators)):
            while operators:
                operands.append(perform_operation(operands, operators.pop()))
            operators.append(item)
        elif is_operator(item):
            operators.append(item)
        else:
            result = parse(item)
            if result:
                operands.append(result)
            else:
                return arg

    while operators:
        operands.append(perform_operation(operands, operators.pop()))
    return operands.pop()


def parse(item):
    if item.startswith("\""):
        return item[1:]
    elif is_int(item):
        return int(item)
    elif is_float(item):
        return float(item)
    elif item.startswith(":"):
        if WS.vars.get(item[1:]):
            return WS.vars.get(item[1:])
        else:
            print "%s HAS NO VALUE" % item[1:]
            raise ValueError('VARIABLE DOESNT EXIST')
    return None


def perform_operation(operands, operator):
    operand2 = operands.pop()
    try:
        operand1 = operands.pop()
    except IndexError:
        return operand2
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
    operators = "()-+*/="
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


def arg_to_list(arg):
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


def return_num_args(func_args):
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
        words = line.split(" ")
        if not in_procedure and words[0] is not "TO":
            WS.vars.update({words[0]: words[1]})
        elif line == "END":
            # WS.proc.update(Procedure(name, args, body))
            in_procedure = False
        else:
            name = words[1]
            args = words[2:]  # if starts with :
            body = []
            in_procedure = True
        # dodati sto ako je u proceduri


def save_in_file(f):
    for proc in WS.proc:
        f.write("TO %s \n %s END \n" % (proc.name, proc.body))
    for var in WS.vars:
        f.write("%s %s \n" % (var, WS.vars[var]))
