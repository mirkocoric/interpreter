from logo_commands import is_int, is_float, str_from_var, is_operator
from logo_commands import is_bool_op, is_paranthesis, perform_operation
from workspace import WS
import custom_exceptions as ce


keywords = ["MAKE", "PR", "INT", "IF", "REPEAT"]


class Token(object):
    def __init__(self, datatype, value):
        self.datatype = datatype
        self.value = value

    def __str__(self):
        return "Type: %s Value: %s" % (self.datatype, self.value)

    __repr__ = __str__


def str_from_op(op):
    func = {"+": "PLUS",
            "-": "MINUS",
            "*": "PROD",
            "/": "DIV",
            "=": "EQUAL",
            "<": "LESS",
            ">": "GREATER",
            "(": "LPAR",
            ")": "RPAR",
            "[": "LUGL",
            "]": "RUGL"
            }
    return func[op]


def parse(item, proc=None):
    if is_int(item):
        return Token("INTEGER", int(item))
    if is_float(item):
        return Token("FLOAT", float(item))
    assert(isinstance(item, str))
    if item.startswith(":"):
        return Token("VAR", item[1:])
    if is_operator(item) or is_paranthesis(item):
        return Token(str_from_op(item), item)
    if item in keywords:
        return Token("KEYWORD", item)
    return Token("STRING", item)


def parse_args(arg, proc=None):
    l = []
    new_item = True
    for ch in arg:
        if not (is_operator(ch) or is_paranthesis(ch)) and not new_item:
            l[-1] += ch
            continue
        new_item = is_operator(ch) or is_paranthesis(ch)
        l.append(ch)
    return [parse(item, proc) for spaced in l for item in spaced.split()]


class Node(object):
    def __init__(self, value, left, right):
        self.value = value
        self.left = left
        self.right = right

    def __str__(self):
        string = str(self.value) + "\n"
        if self.left:
            string += str(self.left)
        if self.right:
            string += str(self.right)
        return string


class AST(object):
    def __init__(self, operand):
        self.root = (operand.root if isinstance(operand, AST)
                     else Node(operand, None, None))

    def add(self, operator, operand):
        old_root = self.root
        self.root = (Node(operator, old_root, operand.root)
                     if isinstance(operand, AST)
                     else Node(operator, old_root, operand))

    def calc(self, root):
        if not isinstance(root, Node):
            return root
        if not is_operator(root.value) or root.left is None:
            return root.value
        return perform_operation([self.calc(root.left), self.calc(root.right)],
                                 root.value)

    def __str__(self):
        return "%s\n%s %s" % (str(self.root.value), str(self.root.left),
                              str(self.root.right))

    __repr__ = __str__


class Interpreter(object):
    def init(self, tokens):
        self.curr_id = 0
        self.peek = tokens[0]

    def next_token(self, tokens):
        if self.curr_id == len(tokens) - 1:
            return Token("END", "END")
        self.curr_id += 1
        self.peek = tokens[self.curr_id]

    def PR(self, tokens):
        return self.expr(tokens)

    def build_ast(self, tokens):
        self.init(tokens)
        if self.peek.datatype == "KEYWORD":
            func = getattr(self, self.peek.value, None)
            return func(tokens[1:])
        return self.expr(tokens)

    def new_layer(self, tokens, separators):
        if separators == ["LESS", "GREATER"]:
            return self.expr(tokens, ["MINUS", "PLUS"])
        if separators == ["MINUS", "PLUS"]:
            return self.expr(tokens, ["PROD", "DIV"])
        if separators == ["PROD", "DIV"]:
            return self.factor(tokens)

    def expr(self, tokens, separators=["LESS", "GREATER"]):
        """EXPR = LAYER1 (< | > LAYER1)*
           LAYER1 = LAYER2 (+ | - LAYER2)*
           LAYER2 = FACTOR (* | / FACTOR)*
           FACTOR = NUMBER | LPAR EXPR RPAR"""
        operand = self.new_layer(tokens, separators)
        ast = AST(operand)
        while self.peek.datatype in separators:
            operator = self.peek.value
            self.next_token(tokens)
            operand = self.new_layer(tokens, separators)
            ast.add(operator, operand)
        return ast

    def factor(self, tokens):
        token = tokens[self.curr_id]
        self.next_token(tokens)
        if token.datatype in ["INTEGER", "FLOAT"]:
            return token.value
        if token.datatype == "LPAR":
            return self.expr(tokens)

def parse_args_test():
    print(parse_args('PR 2 + 4'))
    print(parse_args('IF "TRUE [PR 3]'))
    print(parse_args('IF 2 + 3 > 4 [PR 2]'))
    print(parse_args(' PR (3 +  (4 + 5))'))
    print(parse_args("BLA"))


def build_ast_test():
    it = Interpreter()
    ast1 = it.build_ast(parse_args('PR 2 < 4'))
    ast2 = it.build_ast(parse_args('PR 2 + 4'))
    ast3 = it.build_ast(parse_args('PR 2 + 3 > 4'))
    ast4 = it.build_ast(parse_args('PR 2 < 3 - 4'))
    ast5 = it.build_ast(parse_args('PR 2 + 3 < 4 + 0.4'))
    ast6 = it.build_ast(parse_args('PR 2 + 3 * 4'))
    print(ast1.calc(ast1.root))
    print(ast2.calc(ast2.root))
    print(ast3.calc(ast3.root))
    print(ast4.calc(ast4.root))
    print(ast5.calc(ast5.root))
    print(ast6.calc(ast6.root))


if __name__ == "__main__":
    parse_args_test()
    build_ast_test()



