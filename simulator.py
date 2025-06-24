from enum import Enum


class Instruction:
    def execute(self, interpreter):
        raise NotImplementedError("Subclasses must implement execute")


class PushOp(Instruction):
    def __init__(self, value):
        self.value = value

    def execute(self, interpreter):
        interpreter.execute_push(self.value)

    def __eq__(self, other):
        return isinstance(other, PushOp) and self.value == other.value

    def __str__(self):
        return f"PushOp({self.value})"


class UnaryOp(Instruction, Enum):
    RIGHT = 'right'
    LEFT = 'left'
    REC_LEFT = 'rec_left'
    LEFT_ON_RIGHT = 'left_on_right'
    RIGHT_ON_RIGHT = 'right_on_right'
    UNPAIR = 'unpair'
    Q = 'Q'
    PRINT = 'print'

    def execute(self, interpreter):
        interpreter.execute_unary_op(self)


class BinaryOp(Instruction, Enum):
    PAIR = 'pair'
    ADD = 'add'
    SUB = 'sub'
    MUL = 'mul'
    DIV = 'div'

    def execute(self, interpreter):
        interpreter.execute_binary_op(self)

    def is_numeric(self):
        return self in [BinaryOp.ADD, BinaryOp.SUB, BinaryOp.MUL, BinaryOp.DIV]


class TernaryOp(Instruction, Enum):
    PICK = 'pick'

    def execute(self, interpreter):
        interpreter.execute_ternary_op(self)


class JumpOp(Instruction, Enum):
    JUMP = 'jump'
    QUIT = 'quit'

    def execute(self, interpreter):
        interpreter.execute_jump(self)


class TreeNode:
    pass


class BinaryNode(TreeNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({self.left} :+: {self.right})"

    def __eq__(self, other):
        return isinstance(other, BinaryNode) and self.left == other.left and self.right == other.right


class NilNode(TreeNode):
    def __str__(self):
        return "nil"

    def __eq__(self, other):
        return isinstance(other, NilNode)


class NumberNode(TreeNode):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, NumberNode) and self.value == other.value


class Simulator:
    code: list[Instruction]
    ip: int
    total_steps: int
    tree: TreeNode

    def __init__(self, code: list[Instruction], data: list[int] = None):
        self.code = code
        self.ip = 0
        self.total_steps = 0
        self.tree = NilNode()
        self.data = data or []
        self.output = []

    def run(self):
        while self.ip < len(self.code):
            inst = self.code[self.ip]
            self.execute_instruction(inst)
            self.total_steps += 1

        return self.tree

    def execute_instruction(self, instruction):
        instruction.execute(self)
        if not isinstance(instruction, JumpOp):
            self.ip += 1

    def execute_push(self, value):
        self.tree = BinaryNode(self.tree, value)

    def execute_unary_op(self, op: UnaryOp):
        assert isinstance(self.tree, BinaryNode), f"Operation '{op.value}' requires an argument"
        arg = self.tree.right
        rest = self.tree.left
        match op:
            case UnaryOp.LEFT:
                # left: xs :+: ys ~> xs
                self.tree = rest

            case UnaryOp.RIGHT:
                # right: xs :+: ys ~> ys
                self.tree = arg

            case UnaryOp.REC_LEFT:
                # rec_left: xs :+: n ~> xs :+: ys, where ys is the nth left child of xs
                assert isinstance(arg, NumberNode), "Operation 'rec_left' requires a numeric argument"
                n = arg.value
                result = rest
                for _ in range(n):
                    assert isinstance(result, BinaryNode), "Operation 'rec_left' invoked with too great a depth"
                    result = result.left
                self.tree = BinaryNode(rest, result)

            case UnaryOp.LEFT_ON_RIGHT:
                # left_on_right: xs :+: (ys :+: zs) ~> xs :+: ys
                assert isinstance(arg, BinaryNode), "Operation 'left_on_right' requires a binary argument"
                self.tree = BinaryNode(rest, arg.left)

            case UnaryOp.RIGHT_ON_RIGHT:
                assert isinstance(arg, BinaryNode), "Operation 'right_on_right' requires a binary argument"
                # right_on_right: xs :+: (ys :+: zs) ~> xs :+: zs
                self.tree = BinaryNode(rest, arg.right)

            case UnaryOp.UNPAIR:
                assert isinstance(arg, BinaryNode), "Operation 'unpair' requires a binary argument"
                self.tree = BinaryNode(BinaryNode(rest, arg.left), arg.right)

            case UnaryOp.Q:
                # Q: xs :+: n ~> xs :+: Q(n)
                assert isinstance(arg, NumberNode), "Operation 'Q' requires a numeric argument"
                n = arg.value
                if n < len(self.data):
                    result = self.data[n]
                else:
                    result = 0
                self.tree = BinaryNode(rest, NumberNode(result))

            case UnaryOp.PRINT:
                # print: xs :+: n ~> xs
                self.output.append(chr(arg.value))
                self.tree = rest

    def execute_binary_op(self, op: BinaryOp):
        assert isinstance(self.tree, BinaryNode), f"Operation '{op.value}' requires an argument"
        assert isinstance(self.tree.left, BinaryNode), f"Operation '{op.value}' requires two arguments"
        arg1 = self.tree.right
        arg2 = self.tree.left.right
        rest = self.tree.left.left

        if op.is_numeric():
            assert isinstance(arg1, NumberNode), f"Operation '{op.value}' requires numeric arguments"
            assert isinstance(arg2, NumberNode), f"Operation '{op.value}' requires numeric arguments"

        match op:
            case BinaryOp.PAIR:
                # pair: xs :+: ys :+: zs ~> xs :+: (ys :+: zs)
                self.tree = BinaryNode(rest, BinaryNode(arg2, arg1))

            case BinaryOp.ADD:
                # plus: xs :+: y :+: z ~> xs :+: (z + y)
                result = NumberNode(arg1.value + arg2.value)
                self.tree = BinaryNode(rest, result)

            case BinaryOp.SUB:
                # minus: xs :+: y :+: z ~> xs :+: (z - y)
                result = NumberNode(arg1.value - arg2.value)
                self.tree = BinaryNode(rest, result)

            case BinaryOp.MUL:
                # times: xs :+: y :+: z ~> xs :+: (z * y)
                result = NumberNode(arg1.value * arg2.value)
                self.tree = BinaryNode(rest, result)

            case BinaryOp.DIV:
                # times: xs :+: y :+: z ~> xs :+: (z / y)
                result = NumberNode(arg1.value // arg2.value)
                self.tree = BinaryNode(rest, result)

    def execute_ternary_op(self, op: BinaryOp):
        assert isinstance(self.tree, BinaryNode), f"Operation '{op.value}' requires an argument"
        assert isinstance(self.tree.left, BinaryNode), f"Operation '{op.value}' requires two arguments"
        assert isinstance(self.tree.left.left, BinaryNode), f"Operation '{op.value}' requires three arguments"
        arg1 = self.tree.right
        arg2 = self.tree.left.right
        arg3 = self.tree.left.left.right
        rest = self.tree.left.left.left

        match op:
            case TernaryOp.PICK:
                if arg1.value == 0:
                    self.tree = BinaryNode(rest, arg2)
                else:
                    self.tree = BinaryNode(rest, arg3)

    def execute_jump(self, value: JumpOp):
        match value:
            case JumpOp.JUMP:
                # jump: xs :+: n ~> xs and update IP to be n
                assert isinstance(self.tree, BinaryNode), "Operation 'jump' requires an argument"
                assert isinstance(self.tree.right, NumberNode), "Operation 'jump' requires a numeric argument"
                self.ip = self.tree.right.value
                self.tree = self.tree.left

            case JumpOp.QUIT:
                self.ip = len(self.code)


import re


def build_lookup_table():
    result = {}
    for enum_type in [UnaryOp, BinaryOp, TernaryOp, JumpOp]:
        for enum_member in enum_type:
            result[enum_member.value] = enum_member
    return result


LOOKUP_TABLE = build_lookup_table()


def as_instruction(raw_token):
    if not raw_token:
        raise ValueError("Empty token is not allowed")
    if raw_token.isdigit():
        return PushOp(NumberNode(int(raw_token)))
    if raw_token == 'nil':
        return PushOp(NilNode())
    return LOOKUP_TABLE[raw_token]


def parse(code):
    instructions = []
    for line in code.splitlines():
        if '//' in line:
            line = line[:line.index('//')]
        line = line.strip()
        if line:
            instructions.append(as_instruction(line))
    return instructions


import sys
import argparse


def main(argv):
    arg_parser = argparse.ArgumentParser(description='Tree-lang interpreter')
    arg_parser.add_argument('file', nargs='?', help='Input file (default: stdin)')
    arg_parser.add_argument('-Q', metavar='filename', help='File with whitespace-separated integers')
    args = arg_parser.parse_args(argv[1:])

    if args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        code = sys.stdin.read()

    query_list = None
    if args.Q:
        with open(args.Q, 'r') as f:
            query_list = [int(x) for x in f.read().split()]

    program = parse(code)
    interpreter = Simulator(program, query_list)
    interpreter.run()
    print(f'ran in {interpreter.total_steps} steps')
    if isinstance(interpreter.tree, BinaryNode):
        if isinstance(interpreter.tree.right, NumberNode):
            print(f"result: {interpreter.tree.right.value}")
    if interpreter.output:
        print(''.join(interpreter.output))


if __name__ == "__main__":
    main(sys.argv)
