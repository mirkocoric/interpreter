from util import print_list


def str_error(err, item):
    return (err + str(item) if not isinstance(item, list)
            else err + "[" + print_list(item) + "]")


class ParseError(Exception):
    def __init__(self, message=None):
        self.message = message


class ExecutionEnd(Exception):
    def __init__(self, message=None):
        self.message = message


class InterruptProc(Exception):
    def __init__(self, message=None):
        self.message = message


class CanOnlyInProcError(ParseError):
    def __init__(self):
        self.message = "CAN ONLY DO THAT IN A PROCEDURE"


class NotEnoughInputsError(ParseError):
    def __init__(self, func):
        self.message = "NOT ENOUGH INPUTS TO %s" % func


class ArgumentError(ParseError):
    def __init__(self, func, item):
        self.message = str_error("%s DOESN'T LIKE " % func, item) + " AS INPUT"


class ExtraArgumentError(ParseError):
    def __init__(self, item):
        self.message = str_error("I DON'T KNOW WHAT TO DO WITH ", item)


class UndefinedError(ParseError):
    def __init__(self, item):
        self.message = str_error("I DON'T KNOW HOW TO ", item)
