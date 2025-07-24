"""
Provides structure for loading program onto board
and executing
"""
from assemble import Assemble

class RegState(dict):
    @classmethod
    def default(cls, stack_pointer = 0x8000_0000):
        rs = cls()
        rs[1] = stack_pointer
        return rs
        
class AddressMap(object):
    CPU = 0x0000_0000
    RAM = 0x8000_0000
        
class RegisterMap(object):
    CPU_RUN_MODE = 0x00 + AddressMap.CPU
    REG_BASE     = 0x01 + AddressMap.CPU
    PC           = 0x21 + AddressMap.CPU

class ExecProgram(object):
    def __init__(
        self,
        regs = RegState.default(),
        program = None
    ):
        self.regs = regs
        self.program = program
        
    def load_line(self, line):
        if self.program is None:
            self.program = list()
        self.program.append(line)
        
    def write_regs(self, ser):
        for r in self.regs:
            ser.write_long(r + RegisterMap.REG_BASE, self.regs[r])
            
    def assemble(self, lsb=True):
        a = Assemble(self.program)
        
        for w in a.get_words(lsb):
            print("0b{:032b}".format(w))
            yield w
            
    def upload_program(self, ser):
        addr = AddressMap.RAM
        
        for a in self.assemble():
            ser.write_long(addr, a)
            addr += 4 # next address
            
    def step(self, ser):
        # Put into step mode
        ser.write_long(RegisterMap.CPU_RUN_MODE, 1)