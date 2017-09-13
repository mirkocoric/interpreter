
import math
from logo_commands import LogoInterpreter, is_float
from custom_exceptions import ExecutionEnd, ParseError


class TestInterpreter():
    def __init__(self):
        self.it = LogoInterpreter(outstream=True)
        self.ev_gen = None

    def send(self, line, ev_gen=False):
        if not ev_gen:
            self.ev_gen = self.it.execute()
            self.ev_gen.next()
        try:
            self.ev_gen.send(line)
        except StopIteration:
            pass
        except ExecutionEnd:
            pass
        except ParseError as err:
            self.it.PR([], err.message)
        ret = self.it.print_out()
        return ret

    def check(self, line, result, line2=None):
        if is_float(line) and is_float(result):
            if math.fabs(line - result) > 0.0001:
                raise AssertionError("%s != %s" % (line, result))
            else:
                print("OK")
        elif line == result or (line2 is not None and line2 == result):
            print "OK"
        else:
            raise AssertionError("%s != %s" % (line, result))

    def check_line(self, line, result):
        if not isinstance(line, list):
            raise AssertionError("%s IS NOT LIST" % line)
        for ind in xrange(len(line)):
            if not is_float(line[ind]):
                raise AssertionError("%s IS NOT INTEGER" % line[ind])
        self.check(line[0], result.getP1().getX())
        self.check(line[1], result.getP1().getY())
        self.check(line[2], result.getP2().getX())
        self.check(line[3], result.getP2().getY())

    def test_fib(self):
        result = self.send('LOAD "TEST10')
        self.check(None, result)
        result = self.send('PR FIBONACCI 1')
        self.check(1, result)
        result = self.send('PR FIBONACCI 2')
        self.check(2, result)
        result = self.send('PR FIBONACCI 4')
        self.check(5, result)

    def basic_test(self):
        result = self.send('PR 2 + 4')
        self.check(6, result)
        result = self.send('PR 2 + 4 * 3')
        self.check(14, result)
        result = self.send('IF "TRUE [PR 3]')
        self.check(3, result)
        result = self.send('IF 2 + 3 > 4 [PR 2]')
        self.check(2, result)
        result = self.send(' PR (3 +  (4 + 5))')
        self.check(12, result)
        result = self.send('PR [2 3 4]')
        self.check("2 3 4", result)
        result = self.send('REPEAT 3 [PR 2 PR 3]')
        self.check([2, 3, 2, 3, 2, 3], result)

    def stripname_test(self):
        result = self.send('LOAD "TEST4')
        self.check(None, result)
        result = self.send("STRIPNAME [] []")
        self.check(None, result)

    def animal_test(self):
        result = self.send('LOAD "ANIMALAPP')
        self.check(None, result)
        result = self.send('ANIMAL')
        self.check(["LET'S PLAY A GAME.", "CHOOSE A RANDOM ANIMAL",
                    "I'M GONNA TRY TO GUESS IT BY",
                    "ASKING QUESTIONS, AND YOU GIVE ME YES OR NO ANSWERS.",
                    "OK, LET'S GO.",
                    "DOES THIS ANIMAL HAVE HORNS"], result)
        result = self.send("YES", True)
        self.check("IS IT A BULL", result)
        result = self.send("YES", True)
        self.check("THAT WAS FUN. WANNA TRY AGAIN?", result,
                   ["LOGO MUST BE A GREAT LANGUAGE.",
                    "THAT WAS FUN. WANNA TRY AGAIN?"])
        result = self.send("YES", True)
        self.check("DOES THIS ANIMAL HAVE HORNS", result)
        result = self.send("NO", True)
        self.check(["WELL, I AM NOT TOO SHARP TODAY.",
                    "I GIVE UP.", "JUST WHAT KIND OF BEAST",
                    "DID YOU HAVE IN MIND?"], result)
        result = self.send("ELEPHANT", True)
        self.check(["TELL ME SOMETHING SPECIAL", "ABOUT AN ELEPHANT"], result)
        result = self.send("ELEPHANT IS GRAY", True)
        self.check("THAT WAS FUN. WANNA TRY AGAIN?", result,
                   ["LOGO MUST BE A GREAT LANGUAGE.",
                    "THAT WAS FUN. WANNA TRY AGAIN?"])
        result = self.send("YES", True)
        self.check("IS THIS ANIMAL GRAY", result)
        result = self.send("YES", True)
        self.check("IS IT AN ELEPHANT", result)
        result = self.send("YES", True)
        self.check("THAT WAS FUN. WANNA TRY AGAIN?",  result,
                   ["LOGO MUST BE A GREAT LANGUAGE.",
                    "THAT WAS FUN. WANNA TRY AGAIN?"])
        result = self.send("NO", True)
        self.check(None, result)

    def koch_test(self):
        result = self.send('LOAD "KOCH')
        self.check(None, result)
        result = self.send('KOCH 6')
        self.check(7, len(self.it.objects))
        self.check_line([250, 250, 250, 245], self.it.objects[0])
        self.check_line([250, 245, 250, 245], self.it.objects[1])
        self.check_line([250, 245, 246.4644, 241.4644], self.it.objects[2])
        self.check_line([246.4644, 241.4644, 246.4644, 241.4644],
                        self.it.objects[3])
        self.check_line([246.4644, 241.4644, 250, 237.9289],
                        self.it.objects[4])
        self.check_line([250, 237.9289, 250, 237.9289],
                        self.it.objects[5])
        self.check_line([250, 237.9289, 250, 232.9289],
                        self.it.objects[6])


if __name__ == "__main__":
    TestInterpreter().basic_test()
    TestInterpreter().test_fib()
    TestInterpreter().stripname_test()
    TestInterpreter().animal_test()
    TestInterpreter().koch_test()
