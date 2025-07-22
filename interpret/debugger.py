"""
Used for printing various system information
"""
from interpret.exec import RegisterMap

class Debugger(object):
    def __init__(self, ser):
        self.ser = ser
        
    def get_reg(self, i):
        addr, data = self.ser.read_long(i + RegisterMap.REG_BASE)
        return data
        
    def get_run_mode(self):
        addr, data = self.ser.read_long(RegisterMap.CPU_RUN_MODE)
        match data:
            case 0:
                return "STOP"
            case 1:
                return "STEP"
            case 2:
                return "CONTINUE"
            case 3:
                return "ERROR"
            case _:
                return "UNKNOWN"
        
    def get_pc(self):
        addr, data = self.ser.read_long(RegisterMap.PC)
        return data
        
        
    def display_state(self):
        print("PC: 0x{}".format(self.get_pc()))
        
        print("State: {}".format(self.get_run_mode()))
    
        spacers = "\t\t\t\t\t\t\t\n"
        
        for i in range(32):
            print("x{:02X}: 0x{:08X}".format(i, self.get_reg(i)), end=spacers[i % len(spacers)])