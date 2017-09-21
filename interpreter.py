from logo_commands import LogoInterpreter
import custom_exceptions as ce


CMDS = LogoInterpreter()


def start_interpreter():
    """Starts Logo interpreter"""
    while True:
        try:
            user_input = CMDS.read_gen.next()
            if user_input.startswith("TO "):
                CMDS.create_proc(user_input)
            else:
                execute(user_input)
        except ce.ParseError as err:
            CMDS.PR([], err.message)
        finally:
            CMDS.print_out()


def execute(user_input):
    ev_gen = CMDS.create_gen()
    while True:
        try:
            ev_gen.send(user_input)
            CMDS.print_out()
            user_input = CMDS.read_gen.next()
        except StopIteration:
            break
        except ce.ExecutionEnd as exec_end:
            if exec_end.message is not None:
                raise ce.ExtraArgumentError(exec_end.message)
            break


if __name__ == "__main__":
    start_interpreter()
