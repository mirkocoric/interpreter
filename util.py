from collections import namedtuple
import re
from workspace import WS
from inspect import getargspec

Var = namedtuple('Var', 'name value')
Command = namedtuple('Command', 'name args')
Procedure = namedtuple('Procedure', 'body args vars')


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
                    return None
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
            elif WS.proc.get(item):
                operators.append(WS.proc.get(item))
            else:
                if not item.startswith(":"):
                    print_parse_error(item)
                return None

    while operators:
        operands.append(perform_operation(operands, operators.pop()))
    return operands.pop()


def print_parse_error(item):
    print ("I DON'T KNOW WHAT TO DO WITH %s"
           % item)


def print_undefined(item):
    print "I DON'T KNOW HOW TO %s" % item


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


def check_num_args(func_args, args):
    n_args = len(func_args.args) - 2
    if len(args) < n_args:
        print "Not enough arguments"
        return False
    if func_args.varargs:
        n_args += len(func_args.varargs)
    if len(args) > n_args:
        print_parse_error(args[n_args])
        return False
    return True


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


def split_line(line):
    """Returns list of commands for each line"""
    # jednostavna verzija bez ugnje\denih naredbi,
    # funkcija bi trebala vratiti listu jenostavnih naredbi za izvrsavanje
    args = line.split(" ")
    return [Command(name=args[0], args=args[1:])]
