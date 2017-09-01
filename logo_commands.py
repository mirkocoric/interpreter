from __future__ import print_function
from __future__ import division
from collections import namedtuple
import os.path
import gc
import math
import pickle
import logging
import time
from itertools import chain
from random import randint
from inspect import getargspec
from workspace import WS
from graphics import *


Var = namedtuple('Var', 'name value')
Command = namedtuple('Command', 'name args')
Procedure = namedtuple('Procedure', 'body args vars')

TEST_VAR = ":TEST"
logging.basicConfig(filename='example.log', level=logging.DEBUG)


class LogoCommands(object):
    def __init__(self):
        self.win = GraphWin("Turtle", 500, 500, autoflush=False)
        self.cooX = 250
        self.cooY = 250
        self.degree = 0
        self.objects = []
        self.pen = True
        self.turtle = None
        self.drawturtle = True
        self.drawn = False
        self.n_drawn = 0
        self.time_drawn = time.time()

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
            if result is not None:
                return result

    def divide_and_execute(self, proc, line):
        lines = self.divide(proc, line)
        for line in lines:
            result = self.execute(proc, line)
            if result is not None:
                return result

    def divide(self, proc, line):
        #line = calc_expr(proc, line)
        # if not isinstance(line, list):
        #    return [line]
        line = (item for item in line)
        lines = []
        curr_list = []
        for item in line:
            curr_list.append(item)
            if self.is_procedure(item):
                line, curr_list = self.add_procedure(line, curr_list, item)
            else:
                print_parse_error(item)
            lines.append(curr_list)
            curr_list = []
        if curr_list:
            lines.append(curr_list)
        return lines

    def add_procedure(self, line, curr_list, item):
        for _ in xrange(self.max_args(item)):
            try:
                arg = line.next()
            except:
                return line, curr_list
            curr_list.append(arg)
            if self.is_procedure(arg):
                line, curr_list = self.add_procedure(line, curr_list, arg)
        return line, curr_list

    def is_procedure(self, name):
        if not isinstance(name, str):
            return False
        return getattr(self, str(name), None) or name in WS.proc

    def max_args(self, name):
        if getattr(self, name, None):
            func = getattr(self, name, None)
            min_args, opt_args = n_args((getargspec(func)))
            return min_args + opt_args
        elif name in WS.proc:
            return len(WS.proc[name].args)

    def execute(self, proc, line):
        if not line:
            return
        logging.debug(line)
        try:
            parsed_line = self.parse_line(proc, line)
        except ValueError:
            return "ERROR"
        logging.debug(parsed_line)
        arg_stack = []
        for parsed_item in reversed(parsed_line):
            if (isinstance(parsed_item, list) and parsed_item and
                    parsed_item[0] == "EXECUTE"):
                arg_stack.append(self.execute(proc, parsed_item[1:]))
            elif str(parsed_item).startswith("\""):
                arg_stack.append(parsed_item[1:])
            elif not isinstance(parsed_item, str):
                arg_stack.append(parsed_item)
            elif is_operator(parsed_item):
                arg_stack.append(parsed_item)
            elif getattr(self, str(parsed_item), None):
                func = getattr(self, parsed_item, None)
                args = []
                min_args, opt_args = n_args((getargspec(func)))
                func_ret = parsed_item not in ["MAKE", "PR", "IF"]
                try:
                    while(len(args) < min_args):
                        arg = arg_stack.pop()
                        if is_operator(arg):
                            arg_stack.append(arg)
                            arg = args.pop()
                            arg_stack, args = check_operator(proc, arg_stack,
                                                             arg, args,
                                                             func_ret)
                        elif len(args) == min_args - 1:
                            arg_stack, args = check_operator(proc, arg_stack,
                                                             arg, args,
                                                             func_ret)
                        else:
                            args.append(arg)
                except IndexError:
                    print("NOT ENOUGH INPUTS TO %s" % parsed_item)
                    return "ERROR"
                try:
                    for _ in xrange(opt_args):
                        args.append(arg_stack.pop())
                except IndexError:
                    pass
                try:
                    result = func(proc, *args)
                    if (str(parsed_item) == "OUTPUT" or
                        str(parsed_item) == "STOP" or
                        str(parsed_item) == "ERROR" or
                        (str(parsed_item).startswith("IF") and
                            result is not None)):
                        return result
                    elif result is not None:
                        arg_stack.append(result)
                except ValueError:
                    return "ERROR"
            elif parsed_item in WS.proc:
                proc_cpy = WS.proc[parsed_item]
                new_proc = Procedure(proc_cpy.body, proc_cpy.args, {})
                args = []
                try:
                    while(len(args) < len(new_proc.args)):
                        arg = arg_stack.pop()
                        if is_operator(arg):
                            arg_stack.append(arg)
                            arg = args.pop()
                            arg_stack, args = check_operator(proc, arg_stack,
                                                             arg, args, True)
                        elif len(args) == len(new_proc.args) - 1:
                            arg_stack, args = check_operator(proc, arg_stack,
                                                             arg, args, True)
                        else:
                            args.append(arg)
                    # logging.debug(parsed_item)
                    for arg in reversed(new_proc.args):
                        new_proc.vars[arg] = args.pop()
                        # logging.debug(new_proc.vars[arg])
                except IndexError:
                    print("NOT ENOUGH INPUTS TO %s" % parsed_item)
                    return "ERROR"
                result = self.exec_proc(new_proc)
                if result == "STOP" or result == "ERROR":
                    pass
                elif result is not None:
                    arg_stack.append(result)
            else:
                try:
                    print_undefined(parsed_item)
                except ValueError:
                    return "ERROR"

        if arg_stack:
            expr = calc_expr(proc, arg_stack)
            return expr

    def parse_line(self, proc, line):
        """Returns parsed line"""
        if not isinstance(line, list):
            line = parse_space_list(line)
        parsed_args = connect_operators([parse_args(proc, arg) for arg in line])
        return [calc_expr(proc, arg) for arg in parsed_args]

    def LOAD(self, proc, f_name):
        if not isinstance(f_name, str):
            print_argument_error("LOAD", f_name)
        elif not os.path.isfile(f_name):
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
            proc.vars[var] = None
        else:
            print("CAN ONLY DO THAT IN A PROCEDURE")
            raise ValueError

    def STOP(self, proc):
        if proc:
            return "STOP"
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
        if proc:
            if name in proc.vars:
                proc.vars[name] = value
                return
        WS.vars[name] = value

    def NAME(self, proc, value, name):
        self.MAKE(proc, name, value)

    def PONS(self, proc):
        print_variables()
        if proc:
            print_local_variables(proc)

    def POALL(self, proc):
        for proc in WS.proc:
            print_procedure(proc, WS.proc[proc])
        for var in WS.vars:
            print_variables()

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
        elif isinstance(value, bool):
            if value:
                print("TRUE")
            else:
                print("FALSE")
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
        return not self.LISTP(proc, arg1)

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
        if arg2 is not None:
            var.append(arg2)
        return var

    def SE(self, proc, arg1, arg2=None):
        if isinstance(arg1, list):
            var = list(arg1)
        else:
            var = [arg1]
        if isinstance(arg2, list):
            for item in arg2:
                var.append(item)
        elif arg2:
            var.append(arg2)
        return var

    def SENTENCE(self, proc, arg1, arg2=None):
        return self.SE(proc, arg1, arg2)

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
        return self.BUTFIRST(proc, arg1)

    def BUTLAST(self, proc, arg1):
        if not arg1:
            print_argument_error("BUTLAST", arg1)
        if not isinstance(arg1, list):
            return str(arg1)[:-1]
        return arg1[:-1]

    def BL(self, proc, arg1):
        return self.BUTLAST(proc, arg1)

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
                return self.divide_and_execute(proc, arg1)
        elif arg2:
            return self.divide_and_execute(proc, arg2)

    def REPEAT(self, proc, num, arg1):
        if not isinstance(num, int):
            print_argument_error("REPEAT", num)
        if not(isinstance(arg1, list)):
            print_argument_error("REPEAT", arg1)
        for _ in xrange(num):
            result = self.divide_and_execute(proc, arg1)
            if result:
                break

    def NOT(self, proc, pred):
        return not check_pred(pred)

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
                    return self.divide_and_execute(proc, lst)
        elif TEST_VAR in WS.vars:
            if WS.vars[TEST_VAR]:
                return self.divide_and_execute(proc, lst)

    def IFFALSE(self, proc, lst):
        if proc:
            if TEST_VAR in proc.vars:
                if not proc.vars[TEST_VAR]:
                    return self.divide_and_execute(proc, lst)
        elif TEST_VAR in WS.vars:
            if not WS.vars[TEST_VAR]:
                return self.divide_and_execute(proc, lst)

    def SHOWTURTLE(self, proc):
        self.drawturtle = True
        self.drawTurtle(proc, self.cooX, self.cooY)

    def ST(self, proc):
        self.SHOWTURTLE(proc)

    def HIDETURTLE(self, proc):
        self.turtle.undraw()
        self.drawn = False
        self.drawturtle = False

    def FORWARD(self, proc, distance):
        x_ch = distance * self.SIN(proc, self.degree)
        y_ch = distance * self.COS(proc, self.degree)
        self.drawTurtle(proc, self.cooX + x_ch, self.cooY - y_ch)

    def FD(self, proc, distance):
        return self.FORWARD(proc, distance)

    def BACK(self, proc, distance):
        x_ch = distance * self.SIN(proc, self.degree)
        y_ch = distance * self.COS(proc, self.degree)
        self.drawTurtle(proc, self.cooX - x_ch, self.cooY + y_ch)

    def BK(self, proc, distance):
        return self.BACK(proc, distance)

    def LEFT(self, proc, degree):
        self.degree -= degree
        if self.degree < -180:
            self.degree += 360
        self.drawTurtle(proc, self.cooX, self.cooY)

    def LT(self, proc, distance):
        return self.LEFT(proc, distance)

    def RIGHT(self, proc, degree):
        self.degree += degree
        if self.degree > 180:
            self.degree -= 360
        self.drawTurtle(proc, self.cooX, self.cooY)

    def RT(self, proc, distance):
        return self.RIGHT(proc, distance)

    def CLEARSCREEN(self, proc):
        self.HOME(proc)
        for line in self.objects:
            line.undraw()
        self.SHOWTURTLE(proc)

    def CS(self, proc):
        self.CLEARSCREEN(proc)

    def HOME(self, proc):
        self.SETPOS(proc, [0, 0])
        self.SETHEADING(proc, 0)

    def SETPOS(self, proc, lst):
        self.drawTurtle(proc, lst[0] + 250, lst[1] + 250)

    def SETX(self, proc, X):
        self.drawTurtle(proc, X + 250, self.cooY)

    def SETY(self, proc, Y):
        self.drawTurtle(proc, self.cooX, Y + 250)

    def SETHEADING(self, proc, degree):
        self.degree = degree
        self.drawTurtle(proc, self.cooX, self.cooY)

    def PENDOWN(self, proc):
        self.pen = True

    def PENUP(self, proc):
        self.pen = False

    def HEADING(self, proc):
        return self.degree

    def update(self):
        if time.time() - self.time_drawn > 1 / 100:
            update()
            self.time_drawn = time.time()

    def hideTurtle(self):
        if self.turtle:
            self.turtle.undraw()
        self.update()

    def drawTurtle(self, proc, X, Y):
        if self.pen:
            line = Line(Point(self.cooX, self.cooY),
                        Point(X, Y))
            self.objects.append(line)
            line.draw(self.win)
        if X > 500:
            X -= 500
        if Y > 500:
            Y -= 500
        if X < 0:
            X += 500
        if Y < 0:
            Y += 500
        dX = X - self.cooX
        dY = Y - self.cooY
        self.cooX = X
        self.cooY = Y
        if self.drawturtle:
            X1 = self.cooX - 20 * self.SIN(proc, self.degree + 30)
            Y1 = self.cooY + 20 * self.COS(proc, self.degree + 30)
            X2 = self.cooX - 20 * self.SIN(proc, self.degree - 30)
            Y2 = self.cooY + 20 * self.COS(proc, self.degree - 30)
            if self.drawn:
                self.turtle.move(dX, dY)
            else:
                self.turtle = Polygon(
                    Point(self.cooX, self.cooY), Point(
                        X1, Y1), Point(X2, Y2))
                self.turtle.draw(self.win)
                self.drawn = True
        self.update()


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


def print_variables():
    for var in WS.vars:
        if isinstance(var, list):
            print ("%s IS [", end=" ")
            for item in var:
                print (item, end=" ")
            print("]")
        else:
            print ("%s IS %s" % (var, WS.vars[var]))


def print_local_variables(proc):
    for var in proc.vars:
        if isinstance(var, list):
            print ("%s IS [", end=" ")
            for item in var:
                print (item, end=" ")
            print("]")
        else:
            print ("%s IS %s" % (var, proc.vars[var]))


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
        if isinstance(name, bool):
            return False
        float_name = float(name)
        int_name = int(float_name)
        if int_name == float_name:
            return True
        return False
    except:
        return False


def is_float(name):
    """Returns True if it is possible to convert string to float"""
    if isinstance(name, bool):
        return False
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


def check_operator(proc, arg_stack, arg, args, func_ret):
    old_arg_stack = list(arg_stack)
    try:
        arg_stack = add_arg_check_operator(proc, arg_stack, arg, func_ret)
        args.append(arg_stack.pop())
        return arg_stack, args
    except:
        args.append(arg)
        arg_stack = old_arg_stack
        return arg_stack, args


def add_arg_check_operator(proc, arg_stack, new_item, func_ret):
    if not arg_stack:
        arg_stack.append(new_item)
        return arg_stack
    top = arg_stack.pop()
    if (is_operator(top) and not is_paranthesis(top) and
        not isinstance(new_item, list) and not (func_ret and is_bool_op(top))):
        item = []
        while(is_operator(top) and not is_paranthesis(top)):
            item.append(new_item)
            item.append(top)
            try:
                new_item = arg_stack.pop()
            except:
                break
            try:
                top = arg_stack.pop()
                if not is_operator(top):
                    arg_stack.append(top)
                    item.append(new_item)
                    break
            except:
                item.append(new_item)
                break
        arg_stack.append(calc_expr(proc, item))
    else:
        arg_stack.append(top)
        arg_stack.append(new_item)
    return arg_stack


def connect_operators(line):
    """line - list of parameters"""
    parsed_line = [line[0]]
    for item in line:
        if isinstance(item, list):
            return line
    for ind in xrange(len(line) - 1):
        if not line[ind + 1] or not line[ind]:
            parsed_line.append(line[ind + 1])
        elif is_operator(parsed_line[-1][-1]) and is_bool_op(line[ind + 1][0]):
            print("NOT ENOUGH INPUTS TO %s" % line[ind + 1][0])
            raise(ValueError)
        #elif (isinstance(parsed_line[-1], list) or
        #len(line) > ind + 2 and isinstance(line[ind + 2][0], list)):
        elif (is_operator(parsed_line[-1][-1]) or
              (is_operator(line[ind + 1][0]) and (not line[ind + 1][0] == "(" and
                                                  not line[ind + 1][0] == "-"))):
            if ((is_bool_op(line[ind + 1][0]) and len(parsed_line) > 1 and
                (isinstance(parsed_line[-2][0], str)) and
                (not parsed_line[-2][0].startswith("\"") and
                not is_operator(parsed_line[-2][0]) and
                parsed_line[-2][0] not in ["MAKE", "PR", "IF"]))) or (
                len(line) > ind + 2 and isinstance(line[ind + 2][0], str) and
                not line[ind + 2][0].startswith("\"") and
                not is_operator(line[ind + 2][0])):
                    return line
            elif not isinstance(line[ind + 1], str):
                for item in line[ind + 1]:
                    parsed_line[-1].append(item)
            else:
                parsed_line[-1] += line[ind + 1]
        else:
            parsed_line.append(line[ind + 1])
    return parsed_line


def parse_space_list(line):
    args = []
    if isinstance(line, int) or isinstance(line, float):
        return [line]
    line = (ch for ch in line)
    operand = ""
    for ch in line:
        if ch == "[":
            args.append(parse_list(line))
        elif ch == "(":
            lst = ["EXECUTE"]
            for item in parse_space_list(line):
                lst.append(item)
            if len(lst) > 1:
                args.append(lst)
        elif ch == ")":
            if operand:
                args.append(operand)
            return args
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
    if op:
        lst.append(convert(op))
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
    """expr is list of operators, it is single item if ther is no operators"""
    operators = []
    operands = []
    ret_expr = []
    last_num = False
    negative = False
    #print(expr)
    if len(expr) == 1 and is_operator(expr[0]):
        return expr[0]
    if not any(is_operator(item) for item in expr):
        if isinstance(expr, list):
            return expr[0]
        else:
            return parse(proc, expr)
    if any(isinstance(item, list) for item in expr):
        #print(expr[0])
        return expr
    #if isinstance(expr, str):
    #   check_valid(expr)
    chs = (ch for ch in expr)
    for item in chs:
        if isinstance(item, list):
            operands.append(item)
        elif item == ")":
            while True:
                try:
                    operator = operators.pop()
                except:
                    return expr
                    #u slucaju da se moze kasnije spojiti
                if operator == "(":
                    break
                operands.append(perform_operation(operands, operator))
            last_num = True
        elif is_plus_minus(item) and not last_num:
            if item == "-":
                operands.append(0)
                try:
                    op = parse(proc, chs.next())
                except StopIteration:
                    print("NOT ENOUGH INPUTS TO -")
                    raise ValueError
                operands.append(op)
                operands.append(perform_operation(operands, item))
                last_num = True
        elif (is_plus_minus(item) and
              is_em_prod_div(operators) or
              (is_bool_op(item) and not is_bool_op(operators))):
            while operators:
                operands.append(perform_operation(operands, operators.pop()))
            operators.append(item)
            last_num = False
        elif is_operator(item):
            operators.append(item)
            last_num = False
        else:
            result = parse(proc, item)
            operands.append(result)
            if not isinstance(result, str):
                last_num = True
            else:
                last_num = False
    while operators:
        operands.append(perform_operation(operands, operators.pop()))
    if len(operands) > 1:
        return operands
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
                var = proc.vars.get(item[1:])
                if isinstance(var, str):
                    var = "\"" + var
                return var
        if item[1:] in WS.vars:
            var = WS.vars.get(item[1:])
            if isinstance(var, str):
                var = "\"" + var
            return var
        else:
            print ("%s HAS NO VALUE" % item[1:])
            raise ValueError('VARIABLE DOESNT EXIST')
    else:
        return item


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
    if operator == "<":
        return operand1 < operand2
    if operator == ">":
        return operand1 > operand2


def is_operator(ch):
    operators = "()-+*/=[]<>"
    for operator in operators:
        if ch == operator:
            return True
    return False


def is_paranthesis(ch):
    operators = "()[]"
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


def is_bool_op(ch):
    operators = "<>="
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


def parse_args(proc, arg):
    if not isinstance(arg, str):
        return [arg]
    operand = ""
    l = []
    for ch in arg:
        if is_operator(ch):
            if operand:
                l.append(operand)
                operand = ""
            elif is_bool_op(ch) and l:
                print("NOT ENOUGH INPUTS TO %s" % ch)
                raise(ValueError)
            if ch == "-":
                l.append("+")
            l.append(ch)
        else:
            operand += ch
    if operand:
        l.append(operand)
    return [parse(proc, item) for item in l]


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
        if not words:
            return
        if line.strip() == "END":
            WS.proc[name] = Procedure(body, args, {})
            in_procedure = False
        elif in_procedure:
            body.append(line[:-1])
        elif not in_procedure and words[0] != "TO":
            var = pickle.load(f)
            WS.vars[words[0]] = var
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
        f.write("%s \n" % var)
        pickle.dump(WS.vars[var], f)
