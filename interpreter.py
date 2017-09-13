
from logo_commands import LogoInterpreter, print_parse_error
from custom_exceptions import ParseError, ExecutionEnd
import pdb


def start_interpreter():
    """Starts Logo interpreter"""
    CMDS = LogoInterpreter()
    while(True):
        user_input = CMDS.read_gen.next()
        if user_input.startswith("TO "):
            CMDS.create_proc(user_input)
        else:
            try:
                ev_gen = CMDS.execute()
                ev_gen.next()
                while(True):
                    try:
                        print("Saljem user input %s" % user_input)
                        ev_gen.send(user_input)
                        CMDS.print_out()
                        user_input = CMDS.read_gen.next()
                    except StopIteration:
                        break
                    except ExecutionEnd as exec_end:
                        if exec_end.message:
                            print_parse_error(exec_end.message)
                        break
            except ParseError as err:
                CMDS.PR([], err.message)
            finally:
                CMDS.print_out()


if __name__ == "__main__":
    start_interpreter()
