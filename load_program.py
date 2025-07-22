from serial_monitor import Monitor
from interpret.exec import ExecProgram
from interpret.debugger import Debugger

if __name__ == "__main__":
    m = Monitor("/dev/ttyUSB2")
    
    ep = ExecProgram()
    debug = Debugger(m)
    
    m.write("x".encode("ascii"))
    
    # Write initial regs
    print("Writing initial regs")
    ep.write_regs(m)
    
    # Print out register states
    print("Initial state")
    debug.display_state()
    
    # Let's try a simple program
    ep.load_line("addi x2, x2, 13")
    
    ep.upload_program(m)
    
    ep.step(m)
    
    debug.display_state()