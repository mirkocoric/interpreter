
from logo_commands import LogoInterpreter, raise_parse_error
from custom_exceptions import ParseError, ExecutionEnd, CanOnlyInProcError
import custom_exceptions as ce


CMDS = LogoInterpreter()


def start_interpreter():
    """Starts Logo interpreter"""
    while True:
        user_input = CMDS.read_gen.next()
        if user_input.startswith("TO "):
            CMDS.create_proc(user_input)
        else:
            execute(user_input)


def execute(user_input):
    ev_gen = CMDS.create_gen()
    while True:
        try:
            try:
                ev_gen.send(user_input)
                CMDS.print_out()
                user_input = CMDS.read_gen.next()
            except StopIteration:
                break
            except ExecutionEnd as exec_end:
                if exec_end.message is not None:
                    ce.ExtraArgumentError(exec_end.message)
                break
        except (CanOnlyInProcError, ParseError) as err:
            CMDS.PR([], err.message)
        finally:
            CMDS.print_out()


if __name__ == "__main__":
    start_interpreter()
