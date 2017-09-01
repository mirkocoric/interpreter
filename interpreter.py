from workspace import WS
from logo_commands import LogoCommands
from logo_commands import print_parse_error

CMDS = LogoCommands()


def start_interpreter():
    """Starts Logo interpreter"""
    while(True):
        user_input = raw_input()
        if user_input.startswith("TO "):
            CMDS.create_proc(user_input)
        else:
            result = CMDS.execute(None, user_input)
            if result is not None and result != "ERROR":
                try:
                    print_parse_error(result)
                except ValueError:
                    pass


if __name__ == "__main__":
    start_interpreter()
