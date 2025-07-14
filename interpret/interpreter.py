"""
Forth like interpretation
Attempt to match SAPF as well as possible
"""
from word import *
from env import *

class Interpreter(object):

    # Primitives
    PUSH_INT = ".PUSH" # Can't be an int directly

    def __init__(self):
        self.d = dict()
        
        self.tokens = list()
        
        self.defining = False
        self.def_word = None
        self.definition = Translation()
        
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
            
    def start_definition(self):
        print("Starting definition")
        self.defining = DEFINE_NAME
            
    def end_definition(self):
        print("Ending definition")
        self.insert_word(self.def_word, self.definition.copy())
        #self.definition.clear()
        self.defining = DEFINE_IDLE
            
    def read(self, token):
        if self.defining == DEFINE_BODY:
            if token == ";":
                self.end_definition()
                return None
            else:
                self.definition.push(Word(token))
                return None
        elif self.defining == DEFINE_NAME:
            if token in self.d:
                print("Warning {} already in dictionary", token)
            self.def_word = token
            self.defining = DEFINE_BODY
            return None
        else:
            print(token)
            if token in self.d:
                t = self.d[token]
            else:
                try:
                    a = int(token)
                    t = self.d[Interpreter.PUSH_INT] # push constant
                    t.assign(a)
                except Exception as e:
                    raise e
            
            t.call(self)
            return t
            
    def read_line(self, line):
        result = [self.read(t) for t in line.split(" ")]
        return [r for r in result if r is not None]

if __name__ == "__main__":
    interpret = Interpreter()
    
    setup_env(interpret)
    
    print(interpret.d)
    
    lines = list()
    
    lines += interpret.read_line(": SQUARE DUP * ;")
    print(interpret.d)
    print(interpret.d["SQUARE"])
    lines += interpret.read_line("5 SQUARE .")

                            
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
        f.writelines([str(l) for l in lines])
        
        # End of program
        f.writelines([
                "\t\tli a0, 10\n",
                "\t\tecall\n",
                ".section .rodata\n", # Start of routines
        ])
        
        # Routines
        f.writelines("\n".join([str(i) for i in interpret.common()]))
        
    