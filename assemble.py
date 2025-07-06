class Register(object):
    """
    Register format
    assumes r0, x0
    """
    def __init__(self, arg):
        self.arg = arg
        
    def width(self):
        return 5
    
    def value(self, args):
        v = int(args[self.arg][1:])
        return v
        
class Immediate(object):
    """
    Immediate, TODO: handle sign extension properly
    """
    def __init__(self, arg, start = 0, stop = 31):
        self.arg = arg
        self.start = start
        self.stop = stop
        
    def width(self):
        return (self.stop - self.start) + 1
        
    def value(self, args):
        v = int(args[self.arg]) & 0xFFFF_FFFF
        mask = (1 << (self.width())) - 1
        return (v >> self.start) & mask
        
class Constant(object):
    def __init__(self, v, width):
        self.v = v
        self._width = width
        
    def width(self):
        return self._width
        
    def value(self, *args):
        mask = (1 << (self.width())) - 1
        return self.v & mask

class Definition(object):
    def __init__(self, *args):
        self.args = args
        
    @classmethod
    def arith_imm(cls, function):
        return cls(
            Immediate(arg = 2, stop = 11),
            Register(arg = 1),
            Constant(function, 3),
            Register(arg = 0),
            Constant(0b00100, width = 5),
            Constant(0b11, width = 2)
        )
        
    @classmethod
    def mul(cls, function):
        return cls(
            Constant(1, 7), # muldiv
            Register(arg = 2), # rs2
            Register(arg = 1), # rs1
            Constant(function, 3), #f
            Register(arg = 0), # rd
            Constant(0b01100, width = 5),
            Constant(0b11, width = 2)
        )
        
    def width(self):
        return sum([a.width() for a in self.args])

DefinitionTable = dict()

# TODO add class methods to simplify
# Immediate
DefinitionTable["andi"] = Definition.arith_imm(0b111)
DefinitionTable["addi"] = Definition.arith_imm(0b000)
        
#Multiplcation
DefinitionTable["mul"] =    Definition.mul(0b000)
DefinitionTable["mulh"] =   Definition.mul(0b001)
DefinitionTable["mulhsu"] = Definition.mul(0b010)
DefinitionTable["mulhu"] =  Definition.mul(0b011)

# Storeh
DefinitionTable["sw"] = Definition(
    Immediate(arg = 1, start = 5, stop = 11),
    Register(arg = 0),
    Register(arg = 2),
    Constant(0b010, width = 3),
    Immediate(arg = 1, start = 0, stop = 4),
    Constant(0b01000, width = 5),
    Constant(0b11, width = 2)
)

# Jal
DefinitionTable["jal"] = Definition(
    Immediate(arg = 1, start = 20, stop = 20), # Offset bit mapping
    Immediate(arg = 1, start = 1, stop = 10),
    Immediate(arg = 1, start = 11, stop = 11),
    Immediate(arg = 1, start = 12, stop = 19),
    Register(arg = 0),
    Constant(0b11011, width = 5),
    Constant(0b11, width = 2)
)

for d in DefinitionTable:
    if DefinitionTable[d].width() != 32:
        raise Exception("Check definition for {}, total width is {}, ({})".format(
                d,
                DefinitionTable[d].width(),
                [a.width() for a in DefinitionTable[d].args]
        ))

class Line(object):
    def __init__(self, line):
        self.line = line
        self.label = self.parse_label()
        self._op = self.op()
        self._args = self.args()
        
    def parse_label(self):
        if ":" in self.line:
            return self.line.split(":")[0]
        else:
            return None
        
    def op(self):
        return self.line.split(" ")[0]
        
    def args(self):
        argpar = "".join(self.line.split(" ")[1:])
        args = [a.strip() for a in argpar.split(",")]
        
        argp = list()
        
        # Handle offset
        for a in args:
            if "(" in a and ")" in a:
                s = a.split("(")
                argp.append(s[0])
                argp.append(s[1][:-1])
            else:
                argp.append(a)
                
        return argp
                
    def parse(self, table = DefinitionTable):
        data = 0
        
        print("Parsing {}: {}".format(self._op, self._args))
        
        if self._op in table:
            for a in table[self._op].args:
                data = data << a.width()
                data += a.value(self._args)
            return data
        return None

class ListAssemble(object):
    def __init__(self, reset, get, next):
        self._reset = reset
        self._get = get
        self._next = next
        
        self.keys = dict()
        
        self.keys["%gen%"] = "0"
        
        self.insert_loop()
        
    def insert_loop(self, dest = "r7"):
        offset = -4 * (len(self._get) + len(self._next) + 1)
        self._next.append("jal {},{}".format(dest, offset))
        
    def assemble(self):
        program = self._reset + self._get + self._next
        
        for p in program:
            for k in self.keys:
                p = p.replace(k, self.keys[k])
            
            data = Line(p).parse()
            yield (data >>  0) & 0xFF
            yield (data >>  8) & 0xFF
            yield (data >> 16) & 0xFF
            yield (data >> 24) & 0xFF
        
if __name__ == "__main__":
    my_andi = Line("andi r0, r1, 0")
    
    print("Op: {}, Args: {}".format(my_andi.op(), my_andi.args()))
    print("Parsed: {:032b}".format(my_andi.parse()))
    assert Line("andi r0, r1, 0").parse() == 0b0000_0000_0000_0000_1111_0000_0001_0011
    
    assert Line("andi r1, r1, 0").parse() == 0b0000_0000_0000_0000_1111_0000_1001_0011