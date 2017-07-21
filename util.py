from collections import namedtuple
from workspace import WS
from inspect import getargspec

Var = namedtuple('Var', 'name value')
Command = namedtuple('Command', 'name args')
Procedure = namedtuple('Procedure', 'body args vars')


def calc_expr(arg):
    return arg


def check_num_args(func_args, args):
    n_args = len(func_args.args) - 2
    if len(args) < n_args:
        print "Not enough arguments"
        return False
    if func_args.varargs:
        n_args += len(func_args.varargs)
    if len(args) > n_args:
        print ("I don't know what to do with %s"
               % args[n_args])
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
