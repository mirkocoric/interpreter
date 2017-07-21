import os.path
import util
from workspace import WS
from inspect import getargspec


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

    def execute(self, proc, line):  # MORA BITI U KLASI KAO I NAREDBE
        # razmisliti moguce je da vrijednost ovisi o buducoj naredbi...t
        # treba biti rekurzija
        # SMISLITI REKURZZIJU ALI NAJPRIJE TESTIRATI DA RADI ZA JEDNOSTAVNE NAREDBE
        commands = util.split_line(line)
        for command in commands:
            func = getattr(self, command.name, None)
            if func:
                if util.check_num_args(getargspec(func), command.args):
                    func(proc, *command.args)
            else:
                if not self.exec_proc(command):
                    print("Command %s does not exist" % command.name)

    def load(self, proc, f_name):
        # try:
        f = open(f_name, 'r')
        util.search_file(f)
        # except ValueError:
        #    print ("File not found")
        # finally:
        #    f.close()

    def save(self, proc, f_name):
        if os.path.exists(f_name):
            print("File already exists")
            return
        with open(f_name, 'w') as f:
            util.save_in_file(f)

    def local(self, proc, var):
        if proc:
            proc.vars.update({var, None})
        else:
            print "Can only do that in a procedure"

    def make(self, proc, name, value):
        value = util.calc_expr(value)
        WS.vars.update({name: value})

    def pons(self, proc):
        for var in WS.vars:
            print "%s IS %s" % (var, WS.vars[var])
