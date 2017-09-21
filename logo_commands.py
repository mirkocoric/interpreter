from __future__ import print_function
from __future__ import division
from collections import namedtuple
import os.path
import gc
import math
import pickle
import time
import decorator
from random import randint
from inspect import getargspec
from workspace import WS
from graphics import GraphWin, Line, Point, Polygon
import custom_exceptions as ce
from util import print_list


Var = namedtuple('Var', 'name value')
Command = namedtuple('Command', 'name args')
Procedure = namedtuple('Procedure', 'body args vars')


def validate_args(types):
    @decorator.decorator
    def my_decorator(func, *args, **kwargs):
        def check_args(*args, **kwargs):
            for arg, typ in zip(args[2:], types):
                if type(arg) not in typ:
                    raise ce.ArgumentError(func.__name__, arg)
        check_args(*args, **kwargs)
        return func(*args, **kwargs)
    return my_decorator


@decorator.decorator
def check_arg_empty(func, *args, **kwargs):
    def check_args(*args, **kwargs):
        if not args[2]:
            raise ce.ArgumentError(func.__name__, args[2])
    check_args(*args, **kwargs)
    return func(*args, **kwargs)


class LogoInterpreter(object):
    def __init__(self, read_gen=None, outstream=False):
        self.win_width = 500
        self.win_height = 500
        self.win = GraphWin("Turtle", self.win_width, self.win_height,
                            autoflush=False)
        self.X = self.win_width / 2
        self.Y = self.win_height / 2
        self.degree = 0
        self.objects = []
        self.pen = True
        self.turtle = None
        self.drawturtle = True
        self.drawn = False
        self.n_drawn = 0
        self.time_drawn = time.time()
        self.output = []
        self.outstream = outstream
        self.read_gen = read_gen if read_gen else self.read()

    def print_out(self):
        if self.outstream:
            if not self.output:
                return None
            if len(self.output) == 1:
                return self.output.pop()
            ret = self.output
            self.output = []
            return ret
        for line in self.output:
            print (line)
        self.output = []

    def read(self):
        while True:
            yield raw_input()

    def create_proc(self, line):
        par_line = line.split()
        if len(par_line) == 1:
            raise ce.NotEnoughInputsError("TO")
        f_name = par_line[1]
        if getattr(self, str(par_line[1]), None):
            self.output.append("%s IS A PRIMITIVE" % f_name)
            return
        if str(f_name) in WS.proc:
            self.output.append("%s IS ALREADY DEFINED" % f_name)
            return
        for ind in xrange(2, len(par_line)):
            arg = par_line[ind]
            if not arg.startswith(":"):
                raise ce.ArgumentError("TO", arg)
            par_line[ind] = arg[1:]
        body = []
        while True:
            user_input = self.read_gen.next()
            if user_input is not "END":
                body.append(user_input)
            WS.proc[par_line[1]] = Procedure(body, par_line[2:], {})
            self.output.append("%s DEFINED" % f_name)

    def exec_proc(self, proc, line=None):
        lines = (proc.body if line is None
                 else self.divide(self.parse_line(proc, line)))
        for line in lines:
            try:
                result_gen = self.execute(proc)
                result_gen.next()
                result_gen.send(line)
                while True:
                    received = yield
                    result_gen.send(received)
            except ce.ExecutionEnd as exec_end:
                if exec_end.message:
                    raise ce.ExtraArgumentError(exec_end.message)
                continue
        raise ce.ExecutionEnd()

    def divide(self, line):
        line = (item for item in line)
        lines = []
        curr_list = []
        for item in line:
            if not self.is_procedure(item):
                raise ce.ExtraArgumentError(item)
            curr_list.append(item)
            line, curr_list = self.add_procedure(line, curr_list, item)
            lines.append(curr_list)
            curr_list = []
        if curr_list:
            lines.append(curr_list)
        return lines

    def add_procedure(self, line, curr_list, item):
        for _ in xrange(self.max_args(item)):
            try:
                arg = line.next()
            except StopIteration:
                return line, curr_list
            curr_list.append(arg)
            if self.is_procedure(arg):
                line, curr_list = self.add_procedure(line, curr_list, arg)
        return line, curr_list

    def is_procedure(self, name):
        return getattr(self, str(name), None) or str(name) in WS.proc

    def max_args(self, name):
        if getattr(self, name, None):
            func = getattr(self, name, None)
            min_args, opt_args = n_args(getargspec(func))
            return min_args + opt_args
        if name in WS.proc:
            return len(WS.proc[name].args)

    def execute(self, proc=None):
        line = yield
        if not line:
            raise ce.ExecutionEnd(None)
        arg_stack = []
        for parsed_item in reversed(self.parse_line(proc, line)):
            if is_exec(parsed_item):
                try:
                    result_gen = self.execute(proc)
                    result_gen.next()
                    result_gen.send(parsed_item[1:])
                    while True:
                        line = yield
                        result_gen.send(line)
                except ce.ExecutionEnd as exec_end:
                    result = exec_end.message
                arg_stack.append(result)
                continue
            if str(parsed_item).startswith("\""):
                arg_stack.append(parsed_item[1:])
                continue
            if not isinstance(parsed_item, str):
                arg_stack.append(parsed_item)
                continue
            if is_operator(parsed_item):
                arg_stack.append(parsed_item)
                continue
            if parsed_item in ["READLIST", "READWORD"]:
                read_line = yield
                splited_line = (read_line.split() if parsed_item == "READLIST"
                                else read_line.split()[0])
                arg_stack.append(splited_line)
                continue
            if getattr(self, str(parsed_item), None):
                func = getattr(self, parsed_item, None)
                min_args, opt_args = n_args(getargspec(func))
                args = check_args(proc, arg_stack, min_args, opt_args,
                                  parsed_item)
                if parsed_item in ["IF", "REPEAT"]:
                    if_gen = func(proc, *args)
                    try:
                        if_gen.next()
                        while True:
                            line = yield
                            if_gen.send(line)
                    except ce.ExecutionEnd as exec_end:
                        result = exec_end.message
                    except StopIteration:
                        raise ce.ExecutionEnd()
                result = func(proc, *args)
                if str(parsed_item) in ["OUTPUT", "STOP"]:
                    raise ce.InterruptProc(result)
                if result is not None:
                    arg_stack.append(result)
                continue
            if parsed_item in WS.proc:
                proc_cpy = WS.proc[parsed_item]
                new_proc = Procedure(proc_cpy.body, proc_cpy.args, {})
                args = check_args(proc, arg_stack, len(new_proc.args), 0, True)
                for arg in reversed(new_proc.args):
                    new_proc.vars[arg] = args.pop()
                proc_gen = self.exec_proc(new_proc)
                try:
                    proc_gen.next()
                    while True:
                        line = yield
                        proc_gen.send(line)
                except ce.InterruptProc as inter:
                    result = inter.message
                except ce.ExecutionEnd:
                    result = None
                if result not in [None, "STOP"]:
                    arg_stack.append(result)
                continue
            raise ce.UndefinedError(parsed_item)
        raise (ce.ExecutionEnd(calc_expr(proc, arg_stack))
               if arg_stack else ce.ExecutionEnd())

    def create_gen(self):
        ev_gen = self.execute()
        ev_gen.next()
        return ev_gen

    def parse_line(self, proc, line):
        """Returns parsed line"""
        if not isinstance(line, list):
            line = parse_space_list(line)
        parsed_variables = parse(proc, [parse_args(proc, arg) for arg in line])
        return [calc_expr(proc, arg)
                for arg in connect_operators(parsed_variables)]

    @validate_args(types=[[str]])
    def LOAD(self, proc, f_name):
        if not os.path.isfile(f_name):
            raise ce.UndefinedError(f_name)
        with open(f_name, 'r') as f:
            search_file(f)

    def SAVE(self, proc, f_name):
        if os.path.exists(f_name):
            raise ce.ParseError("FILE ALREADY EXISTS")
        with open(f_name, 'w') as f:
            save_in_file(f)

    def LOCAL(self, proc, var):
        if not proc:
            raise ce.CanOnlyInProcError()
        proc.vars[var] = None

    def STOP(self, proc):
        if not proc:
            raise ce.CanOnlyInProcError()
        return "STOP"

    def OUTPUT(self, proc, value):
        if not proc:
            raise ce.CanOnlyInProcError()
        return value

    def MAKE(self, proc, name, value):
        if proc and name in proc.vars:
            proc.vars[name] = value
            return
        WS.vars[name] = value

    def NAME(self, proc, value, name):
        self.MAKE(proc, name, value)

    def PONS(self, proc):
        self.print_variables()
        if proc:
            self.print_local_variables(proc)

    def POALL(self, proc):
        for proc in WS.proc:
            self.print_procedure(proc, WS.proc[proc])
        self.print_variables()

    def PO(self, proc, name):
        if str(name) not in WS.proc:
            raise ce.ParseError("%s IS UNDEFINED" % name)
        self.print_procedure(name, WS.proc[str(name)])

    def DEFINEDP(self, proc, name):
        return str(name) in WS.proc

    def READLIST(self, proc):
        AssertionError("UNUTAR READLIST")

    def READWORD(self, proc):
        AssertionError("UNUTAR READWORD")

    @validate_args(types=[[int, float]])
    def INT(self, proc, value):
        return int(value)

    def PR(self, proc, value):
        self.output.append(value_to_print(value))

    def RECYCLE(self, proc):
        gc.collect()

    def ERALL(self, proc):
        WS.vars.clear()
        WS.proc.clear()

    def ERASE(self, proc, name):
        try:
            del WS.proc[name]
        except KeyError:
            raise ce.UndefinedError(name)

    @validate_args(types=[[str]])
    def ERN(self, proc, name):
        try:
            del WS.vars[name]
        except KeyError:
            raise ce.UndefinedError(name)

    def ERNS(self, proc):
        WS.vars.clear()

    def ERPS(self, proc):
        WS.proc.clear()

    def ERASEFILE(self, proc, name):
        if not os.path.isfile(name):
            return
        try:
            os.remove(name)
        except OSError:
            raise ce.ParseError("CANNOT ERASE THE FILE")

    def CATALOG(self, proc):
        self.output += [f for f in os.listdir('.') if os.path.isfile(f)]

    @validate_args(types=[[str]])
    def ASCII(self, proc, arg1):
        return ord(arg1[0])

    @validate_args(types=[[int]])
    def CHAR(self, proc, arg1):
        return chr(arg1)

    @validate_args(types=[[list]])
    def COUNT(self, proc, arg1):
        return len(arg1)

    def EMPTYP(self, proc, arg1):
        return not arg1

    def EQUALP(self, proc, arg1, arg2):
        return arg1 == arg2

    def LISTP(self, proc, arg1):
        return isinstance(arg1, list)

    @validate_args(types=[[int, float, str, list, bool], [list]])
    def MEMBERP(self, proc, arg1, arg2):
        return arg1 in arg2

    def WORDP(self, proc, arg1):
        return not self.LISTP(proc, arg1)

    def NUMBERP(self, proc, arg1):
        return is_float(arg1)

    def NAMEP(self, proc, arg1):
        return arg1 in WS.vars

    def THING(self, proc, arg1):
        if arg1 not in WS.vars:
            raise ce.ParseError("%s HAS NO VALUE" % arg1)
        return WS.vars[arg1]

    def OR(self, proc, arg1, arg2):
        return arg1 or arg2

    def AND(self, proc, arg1, arg2):
        return arg1 and arg2

    @validate_args(types=[[int, float], [int, float]])
    def PRODUCT(self, proc, arg1, arg2):
        return arg1 * arg2

    @validate_args(types=[[int, float], [int, float]])
    def SUM(self, proc, arg1, arg2):
        return arg1 + arg2

    @validate_args(types=[[int, float], [int, float]])
    def QUOTIENT(self, proc, arg1, arg2):
        if arg2 == 0:
            raise ce.ParseError("CAN'T DIVIDE BY ZERO")
        return arg1 / arg2

    @validate_args(types=[[int, float]])
    def ARCTAN(self, proc, arg1):
        return math.atan(arg1) * 180 / math.pi

    @validate_args(types=[[int, float]])
    def COS(self, proc, arg1):
        return math.cos(arg1 * math.pi / 180)

    @validate_args(types=[[int, float]])
    def SIN(self, proc, arg1):
        return math.sin(arg1 * math.pi / 180)

    @validate_args(types=[[int, float]])
    def SQRT(self, proc, arg1):
        if float(arg1) < 0:
            raise ce.ArgumentError("SQRT", arg1)
        return math.sqrt(arg1)

    @validate_args(types=[[int], [int]])
    def REMAINDER(self, proc, arg1, arg2):
        return arg1 % arg2

    @validate_args(types=[[int]])
    def RANDOM(self, proc, arg1):
        return randint(0, arg1 - 1)

    def LIST(self, proc, arg1, arg2=None):
        var = [arg1]
        if arg2 is not None:
            var.append(arg2)
        return var

    def SE(self, proc, arg1, arg2=None):
        var = list(arg1) if isinstance(arg1, list) else [arg1]
        return connect(var, arg2)

    def SENTENCE(self, proc, arg1, arg2=None):
        return self.SE(proc, arg1, arg2)

    @validate_args(types=[[int, float, str], [int, float, str]])
    def WORD(self, proc, arg1, arg2=None):
        return str(arg1) + str(arg2) if arg2 else str(arg1)

    @validate_args(types=[[int, float, str, list, bool], [list]])
    def LPUT(self, proc, arg1, arg2):
        return arg2 + [arg1]

    @validate_args(types=[[int, float, str, list, bool], [list]])
    def FPUT(self, proc, arg1, arg2):
        return [arg1] + arg2

    @check_arg_empty
    def FIRST(self, proc, arg1):
        return str_or_list(arg1)[0]

    @check_arg_empty
    def LAST(self, proc, arg1):
        return str_or_list(arg1)[-1]

    @check_arg_empty
    def BUTFIRST(self, proc, arg1):
        return str_or_list(arg1)[1:]

    def BF(self, proc, arg1):
        return self.BUTFIRST(proc, arg1)

    @check_arg_empty
    def BUTLAST(self, proc, arg1):
        return str_or_list(arg1)[:-1]

    def BL(self, proc, arg1):
        return self.BUTLAST(proc, arg1)

    @validate_args(types=[[int], [list]])
    def ITEM(self, proc, item, lst):
        num = int(item)
        if num < 1:
            raise ce.ArgumentError("ITEM", item)
        if num > len(lst):
            raise ce.ParseError("TOO FEW ITEMS IN %s" % lst)
        return lst[num - 1]

    @validate_args(types=[[int, float, list, bool, str], [list], [list]])
    def IF(self, proc, pred, arg1, arg2=[]):
        if check_pred(pred):
            if not arg1:
                return
            try:
                div_and_exec = self.exec_proc(proc, arg1)
                div_and_exec.next()
                while True:
                    line = yield
                    div_and_exec.send(line)
            except ce.ExecutionEnd:
                return
        if not arg2:
            return
        try:
            div_and_exec = self.exec_proc(proc, arg2)
            div_and_exec.next()
            while True:
                line = yield
                div_and_exec.send(line)
        except ce.ExecutionEnd:
            return

    @validate_args(types=[[int], [list]])
    def REPEAT(self, proc, num, arg1):
        for _ in xrange(num):
            div_and_exec = self.exec_proc(proc, arg1)
            try:
                div_and_exec.next()
                while True:
                    line = yield
                    div_and_exec.send(line)
            except ce.ExecutionEnd as exec_end:
                if exec_end.message:
                    break
            except StopIteration:
                continue

    def NOT(self, proc, pred):
        return not check_pred(pred)

    def SHOWTURTLE(self, proc):
        self.drawturtle = True
        self.drawTurtle(proc, self.X, self.Y)

    def ST(self, proc):
        self.SHOWTURTLE(proc)

    def HIDETURTLE(self, proc):
        self.turtle.undraw()
        self.drawn = False
        self.drawturtle = False

    def FORWARD(self, proc, distance):
        x_ch = distance * self.SIN(proc, self.degree)
        y_ch = distance * self.COS(proc, self.degree)
        self.drawTurtle(proc, self.X + x_ch, self.Y - y_ch)

    def FD(self, proc, distance):
        return self.FORWARD(proc, distance)

    def BACK(self, proc, distance):
        x_ch = distance * self.SIN(proc, self.degree)
        y_ch = distance * self.COS(proc, self.degree)
        self.drawTurtle(proc, self.X - x_ch, self.Y + y_ch)

    def BK(self, proc, distance):
        return self.BACK(proc, distance)

    def LEFT(self, proc, degree):
        self.degree -= degree
        if self.degree < -180:
            self.degree += 360
        self.drawTurtle(proc, self.X, self.Y)

    def LT(self, proc, distance):
        return self.LEFT(proc, distance)

    def RIGHT(self, proc, degree):
        self.degree += degree
        if self.degree > 180:
            self.degree -= 360
        self.drawTurtle(proc, self.X, self.Y)

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
        self.drawTurtle(proc, X + 250, self.Y)

    def SETY(self, proc, Y):
        self.drawTurtle(proc, self.X, Y + 250)

    def SETHEADING(self, proc, degree):
        self.degree = degree
        self.drawTurtle(proc, self.X, self.Y)

    def PENDOWN(self, proc):
        self.pen = True

    def PENUP(self, proc):
        self.pen = False

    def HEADING(self, proc):
        return self.degree

    def update(self):
        if not time.time() - self.time_drawn > 1 / 100:
            return
        self.win.update()
        self.time_drawn = time.time()

    def hideTurtle(self):
        if self.turtle:
            self.turtle.undraw()
        self.update()

    def update_coord(self, X, Y):
        if X > self.win_width:
            X -= self.win_width
        if Y > self.win_height:
            Y -= self.win_height
        if X < 0:
            X += self.win_width
        if Y < 0:
            Y += self.win_height
        self.X = X
        self.Y = Y

    def drawTurtle(self, proc, X, Y):
        if self.pen:
            line = Line(Point(self.X, self.Y), Point(X, Y))
            self.objects.append(line)
            line.draw(self.win)
        dX = X - self.X
        dY = Y - self.Y
        self.update_coord(X, Y)
        if not self.drawturtle:
            return
        turtle_size = 20
        pts_angle = 30
        X1 = self.X - turtle_size * self.SIN(proc, self.degree + pts_angle)
        Y1 = self.Y + turtle_size * self.COS(proc, self.degree + pts_angle)
        X2 = self.X - turtle_size * self.SIN(proc, self.degree - pts_angle)
        Y2 = self.Y + turtle_size * self.COS(proc, self.degree - pts_angle)
        if self.drawn:
            self.turtle.move(dX, dY)
            self.update()
            return
        self.turtle = Polygon(
            Point(self.X, self.Y), Point(
                X1, Y1), Point(X2, Y2))
        self.turtle.draw(self.win)
        self.drawn = True
        self.update()

    def print_variable_list(self, name, value):
        self.output.append("%s IS [%s]" % (name, print_list(value)))

    def print_variables(self):
        self.print_local_variables(WS)

    def print_local_variables(self, proc):
        for var in proc.vars:
            if isinstance(proc.vars[var], list):
                self.print_variable_list(var, proc.vars[var])
            else:
                self.output.append("%s IS %s" % (var, proc.vars[var]))

    def print_procedure(self, name, proc):
        self.output.append("TO %s " % name + " ".join(proc.args))
        self.output += proc.body
        self.output.append("END")


def str_or_list(arg):
    return str(arg) if not isinstance(arg, list) else arg


def value_to_print(value):
    if isinstance(value, list):
        return print_list(value)
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def connect(var, arg2):
    if isinstance(arg2, list):
        return var + arg2
    return arg2 if arg2 else var


def is_exec(parsed_item):
    return (isinstance(parsed_item, list) and parsed_item
            and parsed_item[0] == "EXECUTE")


def check_args(proc, arg_stack, min_args, opt_args, parsed_item):
    try:
        args = check_req_args(proc, arg_stack, min_args, parsed_item)
    except IndexError:
        raise ce.NotEnoughInputsError(parsed_item)
    try:
        args = check_opt_args(arg_stack, opt_args, args)
    except IndexError:
        pass
    return args


def check_req_args(proc, arg_stack, min_args, parsed_item):
    args = []
    while(len(args) < min_args):
        arg = arg_stack.pop()
        if is_operator(arg):
            arg_stack.append(arg)
            arg = args.pop()
            arg_stack, args = check_operator(proc, arg_stack, arg, args,
                                             parsed_item)
            continue
        if len(args) == min_args - 1:
            arg_stack, args = check_operator(proc, arg_stack, arg, args,
                                             parsed_item)
            continue
        args.append(arg)
    return args


def check_opt_args(arg_stack, opt_args, args):
    for _ in xrange(opt_args):
        args.append(arg_stack.pop())
    return args


def is_int(name):
    """Returns True if the string is int"""
    if isinstance(name, bool):
        return False
    try:
        return int(name) == float(name)
    except (TypeError, ValueError):
        return False


def is_float(name):
    """Returns True if it is possible to convert string to float"""
    if isinstance(name, bool):
        return False
    try:
        float(name)
        return True
    except (TypeError, ValueError):
        return False


def check_pred(pred):
    if not isinstance(pred, bool) and pred not in ["TRUE", "FALSE"]:
        raise ce.ParseError("%s IS NOT TRUE OR FALSE" % pred)
    return pred and pred != "FALSE"


def check_operator(proc, arg_stack, arg, args, parsed_item):
    old_arg_stack = list(arg_stack)
    func_ret = parsed_item not in ["MAKE", "PR", "IF"]
    try:
        arg_stack = add_arg_check_operator(proc, arg_stack, arg, func_ret)
        args.append(arg_stack.pop())
    except IndexError:
        args.append(arg)
        arg_stack = old_arg_stack
    return arg_stack, args


def should_be_appended(top, new_item, func_ret):
    return (is_operator(top) and not is_paranthesis(top)
            and not isinstance(new_item, list)
            and not (func_ret and is_bool_op(top)))


def add_arg_check_operator(proc, arg_stack, new_item, func_ret):
    if not arg_stack:
        arg_stack.append(new_item)
        return arg_stack
    top = arg_stack.pop()
    if not should_be_appended(top, new_item, func_ret):
        arg_stack += [top, new_item]
        return arg_stack
    item = []
    while is_operator(top) and not is_paranthesis(top):
        item += [new_item, top]
        try:
            new_item = arg_stack.pop()
        except IndexError:
            break
        try:
            top = arg_stack.pop()
            if is_operator(top):
                continue
            arg_stack.append(top)
            item.append(new_item)
            break
        except IndexError:
            item.append(new_item)
            break
    arg_stack.append(calc_expr(proc, item))
    return arg_stack


def border_operators(ch_bf, ch_af):
    return (is_operator(ch_bf) or (is_operator(ch_af) and
                                   (ch_af not in ["(", "-"])))


def is_not_spec_func(func):
    return func not in ["MAKE", "PR", "IF", "OUTPUT", "STOP"]


def func_af(line, ind):
    if len(line) <= ind:
        return False
    first_ch = line[ind][0]
    return (isinstance(first_ch, str)
            and not first_ch.startswith("\"")
            and not is_operator(first_ch)
            and is_not_spec_func(first_ch))


def func_bf(ch_af, parsed_line):
    if len(parsed_line) <= 1:
        return False
    last_ch = parsed_line[-2][0]
    return (is_bool_op(ch_af) and isinstance(last_ch, str)
            and not last_ch.startswith("\"")
            and not is_operator(last_ch)
            and is_not_spec_func(last_ch))


def connect_operators(line):
    """line - list of parameters"""
    for item in line:
        if isinstance(item, list) and is_exec(item[0]):
            return line
    parsed_line = [line[0]]
    for ind in xrange(len(line) - 1):
        next_op = line[ind + 1]
        if not next_op or not line[ind]:
            parsed_line.append(next_op)
            continue
        if is_operator(parsed_line[-1][-1]) and is_bool_op(next_op[0]):
            raise ce.NotEnoughInputsError()(next_op[0])
        if not border_operators(parsed_line[-1][-1], next_op[0]):
            parsed_line.append(next_op)
            continue
        if func_bf(next_op[0], parsed_line) or func_af(line, ind + 2):
            return line
        parsed_line[-1] += next_op
    return parsed_line


def parse_space_list(line):
    args = []
    if isinstance(line, int) or isinstance(line, float):
        return [line]
    line = iter(line)
    operand = ""
    for ch in line:
        if ch == ")":
            return args if not operand else args + [operand]
        if ch == "[":
            args.append(parse_list(line))
        elif ch == "(":
            lst = ["EXECUTE"] + parse_space_list(line)
            if len(lst) > 1:
                args.append(lst)
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
    if is_float(op):
        return float(op)
    return op


def parse_list(expr):
    lst = []
    op = ""
    for ch in expr:
        if op and ch in ["]", " "]:
            lst.append(convert(op))
        if ch == "]":
            return lst
        if ch == "[":
            lst.append(parse_list(expr))
        elif ch == " ":
            op = ""
        else:
            op += ch
    if op:
        lst.append(convert(op))
    return lst


def parse_chs(proc, expr, operands, operators):
    for ch in expr:
        parse_ch(proc, expr, ch, operands, operators)
    return operands, operators


def parse_right_par(operands, operators):
    while True:
        operator = operators.pop()
        if operator == "(":
            break
        operands.append(perform_operation(operands, operator))


def parse_minus(proc, operands, expr):
    operands.append(0)
    try:
        op = parse(proc, expr.next())
    except StopIteration:
        raise ce.NotEnoughInputsError()("-")
    operands.append(op)
    operands.append(perform_operation(operands, "-"))


def is_less_prec(ch, operators):
    return (is_plus_minus(ch) and
            is_em_prod_div(operators) or
            (is_bool_op(ch) and not is_bool_op(operators)))


def parse_ch(proc, expr, ch, operands, operators):
    if isinstance(ch, list):
        operands.append(ch)
    elif ch == ")":
        parse_right_par(operands, operators)
    elif ch == "-":
        parse_minus(proc, operands, expr)
    elif is_less_prec(ch, operators):
        while operators:
            operands.append(perform_operation(operands, operators.pop()))
        operators.append(ch)
    elif is_operator(ch):
        operators.append(ch)
    else:
        result = parse(proc, ch)
        operands.append(result)


def calc_expr(proc, expr):
    """expr is list of operators, it is single item if ther is no operators"""
    operators = []
    operands = []
    first = expr[0]
    if len(expr) == 1 and is_operator(first):
        return first
    if not any(is_operator(item) for item in expr):
        return first if isinstance(expr, list) else parse(proc, expr)
    if any(isinstance(item, list) for item in expr):
        return expr
    operands, operators = parse_chs(proc, iter(expr), operands, operators)
    while operators:
        operands.append(perform_operation(operands, operators.pop()))
    return operands if len(operands) > 1 else operands.pop()


def parse(proc, item):
    if isinstance(item, list):
        return item
    if is_int(item):
        return int(item)
    if is_float(item):
        return float(item)
    if item.startswith(":"):
        var_name = item[1:]
        if proc and var_name in proc.vars:
            return str_from_var(var_name, proc)
        if var_name in WS.vars:
            return str_from_var(var_name, WS)
        raise ce.ParseError("%s HAS NO VALUE" % var_name)
    return item


def str_from_var(var_name, proc):
    var = proc.vars.get(var_name)
    return "\"" + var if isinstance(var, str) else var


def perform_operation(operands, operator):
    try:
        operand2 = operands.pop()
    except IndexError:
        raise ce.NotEnoughInputsError()(operator)
    try:
        operand1 = operands.pop()
    except IndexError:
        return operand2
    if not is_float(operand1):
        raise ce.ArgumentError(operator, operand1)
    if not is_float(operand2):
        raise ce.ArgumentError(operator, operand2)
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
    return str(ch) in "(-+*[/=]<)>"


def is_paranthesis(ch):
    return str(ch) in "]([)"


def is_plus_minus(ch):
    return str(ch) in "-+"


def is_bool_op(ch):
    return str(ch) in "<>="


def is_em_prod_div(operators):
    return not operators or operators[- 1:][0] in "*/"


def parse_args(proc, arg):
    if not isinstance(arg, str):
        return [arg]
    operand = ""
    l = []
    for ch in arg:
        if is_bool_op(ch) and l:
            raise ce.NotEnoughInputsError(ch)
        if not is_operator(ch):
            operand += ch
            continue
        if operand:
            l.append(operand)
            operand = ""
        if ch == "-":
            l.append("+")
        l.append(ch)
    if operand:
        l.append(operand)
    return [parse(proc, item) for item in l]


def n_args(func_args):
    args = len(func_args.args) - 2
    opt_args = len(func_args.defaults) if func_args.defaults else 0
    return args - opt_args, opt_args


def search_file(f):
    in_procedure = False
    while True:
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
