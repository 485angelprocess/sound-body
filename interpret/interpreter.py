"""
Forth like interpretation
Attempt to match SAPF as well as possible
"""
from word import *

class Prim(object):
    def __init__(self, v):
        self.v = v

class Interpreter(object):

    # Primitives
    PUSH_INT = ".PUSH" # Can't be an int directly

    def __init__(self):
        self.d = dict()
        
        self.tokens = list()
        
    def insert_word(self, word, program):
        self.d[word] = program
            
    @staticmethod
    def pop():
        yield Line("lw", R.value(), R.sp(8), label = "POP") # Load data
        yield Line("lw", R.tag(), R.sp(4)) # Load tag
        #yield Line("jalr", R.work(), R.tag(), "0") # If 0 take branch
        yield Line("addi", R.sp(), R.sp(), 8) # increase stack pointer
        yield Line("jalr", R.ret(), R.ret(), 0) # return value
        # TAG greater than N can do arbitary code exploit
        
    @staticmethod
    def push():
        yield Line("sw", R.value(), R.sp(0), label = "PUSH") # Store data
        yield Line("sw", R.tag(), R.sp(-4)) # Store tag
        yield Line("addi", R.sp(), R.sp(), -8) # Increase stack
        yield Line("jalr", R.ret(), R.ret(), 0)
        
    def common(self):
        # POP and PUSH
        for p in Interpreter.pop():
            yield str(p)
        for p in Interpreter.push():
            yield str(p)
            
    def read(self, token):
        if token in self.d:
            t = self.d[token]
        else:
            try:
                a = int(token)
                t = self.d[Interpreter.PUSH_INT] # push constant
                t.assign(a)
            except Exception as e:
                raise e
        
        return t

if __name__ == "__main__":
    interpret = Interpreter()
    
    # Push a constant integer onto the stack
    interpret.insert_word(Interpreter.PUSH_INT, Translation(
            Line("addi", R.value(), R.zero(), Arg(0)),
            Line("addi", R.tag(), R.zero(), Arg(1, default = 0)),
            Line("jalr", R.ret(), "s7", 0),
            desc = "Push onto stack")
    )
    
    interpret.insert_word("+", Translation(
        Line("jalr", R.ret(), "s8", 0),
        Line("addi", R.work(1), R.value(), C(0)), # Copy data to register
        Line("jalr", R.ret(), "s8", 0),
        Line("add", R.value(), R.work(1), R.value()),
        Line("addi", R.tag(), R.zero(), C(0)),
        Line("jalr", R.ret(), "s7", 0)
        , desc = "Add two registers"))
                            
                            
    with open("add.s", "w") as f:
        # Start point
        f.writelines([
                ".section .text\n",
                ".globl _start:\n",
                "\tla s7, PUSH\n",
                "\tla s8, POP\n",
                "\taddi x5, sp, 0\n"
        ])
        
        # Interpreted program
        f.writelines([
                str(interpret.read("5")),
                str(interpret.read("4")),
                str(interpret.read("+")),
        ])
        
        # End of program
        f.writelines([
                "\t\tli a0, 10\n",
                "\t\tecall\n",
                ".section .rodata\n", # Start of routines
        ])
        
        # Routines
        f.writelines("\n".join([str(i) for i in interpret.common()]))
        
    