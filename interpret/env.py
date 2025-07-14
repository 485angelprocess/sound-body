from word import *

DEFINE_IDLE = 0
DEFINE_NAME = 1
DEFINE_BODY = 2

def setup_env(interpret):

    # Builtins
    interpret.insert_word(".PUSH", Translation(
        Line("addi", R.value(), R.zero(), Arg(0)),
        Line("addi", R.tag(), R.zero(), Arg(1, default = 0)),
        Line("jal", R.ret(), C("PUSH")),
        desc = "Push constant int onto stack"
    ))
    
    interpret.insert_word(".POP", Translation(
        Line("jal", R.ret(), C("POP")),
        desc = "POP"
    ))
    
    interpret.insert_word("DUP", Translation(
        Line("lw", R.value(), R.sp(8)),
        Line("lw", R.tag(), R.sp(4)),
        Line("jal", R.ret(), C("PUSH")),
        desc = "duplicate top of stack"
    ))
    
    interpret.insert_word(".", Translation(
        desc = "PRINT (TODO)"
    ))
    
    # Arithmetic
    interpret.insert_word("+", Translation(
        Line("jal", R.ret(), C("POP")),
        Line("addi", R.work(1), R.value(), C(0)), # Copy data to register
        Line("jal", R.ret(), C("POP")),
        Line("add", R.value(), R.work(1), R.value()),
        Line("addi", R.tag(), R.zero(), C(0)),
        Line("jal", R.ret(), C("PUSH"), 0),
        desc = "Add two registers"
    ))
    
    interpret.insert_word("*", Translation(
        Line("jal", R.ret(), C("POP")),
        Line("addi", R.work(1), R.value(), C(0)),
        Line("jal", R.ret(), C("POP")),
        Line("mul", R.value(), R.work(1), R.value()),
        Line("addi", R.tag(), R.zero(), C(0)), # Int type
        Line("jal", R.ret(), C("PUSH"), 0),
        desc = "Multiply two registers"
    ))
    
    # Special
    interpret.insert_word(":", Translation().set_callback(
        lambda ctx: ctx.start_definition()
    ))
    
    interpret.insert_word(";", Translation().set_callback(
        lambda ctx: ctx.end_definition()
    ))