import os.path
import util
from workspace import WS
from inspect import getargspec

# RIJESITI PR INT 4  PR OR ...


class LogoCommands(object):
    def exec_proc(self, command):
        proc = WS.proc.get(command.name)
        if not proc:
            return False
        for argc, argp in zip(command.args, proc.args):
            WS.vars.update({argp: argc})
        for line in proc.body:
            self.execute(line, proc)
        return True

    def execute(self, proc, line):
        commands = util.split_line(line)
        for command in commands:
            func = getattr(self, command.name, None)
            expr = [util.calc_expr(arg) for arg in command.args]
            if func:
                if util.check_num_args(getargspec(func), expr):
                    func(proc, *expr)
            else:
                if not self.exec_proc(command):
                    print("COMMAND %s DOES NOT EXIST" % command.name)

    def LOAD(self, proc, f_name):
        if not os.path.exists(f_name):
            print("FILE NOT FOUND")
            return
        with open(f_name, 'r') as f:
            util.search_file(f)

    def SAVE(self, proc, f_name):
        if os.path.exists(f_name):
            print("FILE ALREADY EXISTS")
            return
        with open(f_name, 'w') as f:
            util.save_in_file(f)

    def LOCAL(self, proc, var):
        if proc:
            proc.vars.update({var, None})
        else:
            print "CAN ONLY DO THAT IN A PROCEDURE"

    def MAKE(self, proc, name, value):
        if value:
            WS.vars.update({name: value})

    def PONS(self, proc):
        for var in WS.vars:
            print "%s IS %s" % (var, WS.vars[var])

    def INT(self, proc, value):
        if util.is_float(value):
            return int(value)
        print "INT DOESN'T LIKE %s AS INPUT"

    def PR(self, proc, value):
        print value
