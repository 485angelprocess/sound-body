"""
Test CPU insruction
"""
import unittest
from amaranth.sim import *
from core.cpu import RiscCore
from interpret.exec import ExecProgram
from infra.ram import WishboneMemory
from infra.signature import Bus

from amaranth import Module
from amaranth.lib import wiring


def core_with_program(program):
    dut = Module()
    
    print("Loading program: ")
    for i in range(len(program)):
        print("\t{:02X}: {:02X}".format(i, program[i]))
    
    dut.submodules.cpu = cpu = RiscCore(has_mul=False, normally_on=True)
    dut.submodules.ram = ram = WishboneMemory(32, 256, init=program, granularity=2)
    
    wiring.connect(dut, cpu.prog, ram.bus)
    
    return dut, cpu.bus

class TestCpu(unittest.TestCase):
    def test_addi(self):
        
        program = [
            "andi r0, r0, 0",
            "andi r1, r1, 0",
            "addi r0, r0, 3",
            "sw r0, 0(r1)"
        ]
        
        ep = ExecProgram(program=program)
        dut, bus = core_with_program(list(ep.assemble()))
        
        async def expect(ctx):
            assert await Bus.write_consume(ctx,bus) == 0,3
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(expect)
        
        with sim.write_vcd("bench/test_addi.vcd") as vcd:
            sim.run_until(100*1e-8)
            
if __name__ == "__main__":
    unittest.main()