from repl import Interpreter


class TestInterpreter():

    def __init__(self):
        self.it = Interpreter(outStream=True)
        self.ev_gen = self.it.evaluate()
        self.ev_gen.next()
        self.line = None

    def send(self, line):
        self.line = line
        self.ev_gen.send(line)

    def check(self, line):
        self.assertEqual(self.it.output()[0], line)

    def assertEqual(self, inn, out):
        if inn == out:
            print "OK"
        else:
            raise AssertionError("%s != %s" % (inn, out))

    def test(self):
        self.send('IME')
        self.check('Kako se zoves?')
        self.send('MIRKO')
        self.check('A prezivas')
        self.send('CORIC')
        self.check('DOBAR DAN MIRKO CORIC')
        self.send('HVALA')
        self.check('HVALA')


if __name__ == "__main__":
    TestInterpreter().test()
