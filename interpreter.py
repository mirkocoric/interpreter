from workspace import WS
from logo_commands import LogoCommands

CMDS = LogoCommands()


def start_interpreter():
    """Starts Logo interpreter"""
    while(True):
        user_input = raw_input()
        if user_input.startswith("TO "):
            CMDS.create_proc(user_input)
        else:
            CMDS.execute(None, user_input)


if __name__ == "__main__":
    start_interpreter()
