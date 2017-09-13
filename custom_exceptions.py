class ParseError(Exception):
    def __init__(self, message=None):
        self.message = message


class ExecutionEnd(Exception):
    def __init__(self, message=None):
        self.message = message


class InterruptProc(Exception):
    def __init__(self, message=None):
        self.message = message
