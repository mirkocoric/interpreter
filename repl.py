
class Interpreter(object):

    def __init__(self, outStream=False):
        self.outLines = []
        self.outStream = outStream

    def read(self):
        while(True):
            yield raw_input()

    def output(self):
        if self.outStream:
            ret = self.outLines
            self.outLines = []
            return ret
        for line in self.outLines:
            print self.outLines.pop()

    def evaluate(self):
        while(True):
            line = yield
            if line == "IME":
                ime = self.start_ime()
                ime.next()
                while True:
                    try:
                        line = yield
                        ime.send(line)
                    except StopIteration:
                        break
            else:
                self.outLines.append(line)

    def start_ime(self):
        self.outLines.append("Kako se zoves?")
        ime = yield
        self.outLines.append("A prezivas")
        prezime = yield
        self.outLines.append("DOBAR DAN %s %s" % (ime, prezime))

    def repl(self, read_gen=None):
        inline = ""
        if not read_gen:
            read_gen = self.read()
        ev_gen = self.evaluate()
        ev_gen.next()
        while(True):
            inline = read_gen.next()
            ev_gen.send(inline)
            self.output()


if __name__ == "__main__":
    it = Interpreter()
    it.repl()
