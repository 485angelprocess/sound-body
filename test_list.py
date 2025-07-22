"""
Test for lazy list computation
"""
import unittest

from amaranth.lib import wiring
from amaranth.sim import *
from amaranth import *

from core.cpu import RiscCore
from infra.ram import WishboneMemory

from assemble import ListAssemble

def core_with_program(program):
    dut = Module()
    
    print("Loading program: ")
    for i in range(len(program)):
        print("\t{:02X}: {:02X}".format(i, program[i]))
    
    dut.submodules.cpu = cpu = RiscCore(has_mul=True)
    dut.submodules.ram = ram = WishboneMemory(32, 256, init=program, granularity=2)
    
    wiring.connect(dut, cpu.prog, ram.bus)
    
    return dut, cpu.bus
    
async def get_gen(ctx, port, addr_expect=0, timeout=10):

    ctx.set(port.ack, 1)
    stb, addr, w_data = await ctx.tick().sample(port.stb, port.addr, port.w_data).until(port.cyc)
    assert addr == addr_expect
    return w_data
    ctx.set(port.ack, 0)

class TestList(unittest.TestCase):
    def test_natural_numbers(self):
        # Clear registers
        # Set r1 to special address
        reset = ["andi r0, r0, 0",
                    "andi r1, r1, 0",
                    "addi r1, r1, %gen%"]
        # Write out value to special add
        get   = ["sw r0, 0(r1)"]
        # Add one to register
        next =  ["addi r0, r0, 1"]
        
        program = list(ListAssemble(reset, get, next).assemble())
        
        dut, out = core_with_program(program)
        
        async def process(ctx):
            for i in range(100):
                assert await get_gen(ctx, out) == i
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(process)
        
        with sim.write_vcd("bench/natural_numbers.vcd") as vcd:
            sim.run()
            
    def test_ord_numbers(self):
        # Clear registers
        # Set r1 to special address
        reset = ["andi r0, r0, 0",
                    "addi r0, r0, 1",
                    "andi r1, r1, 0",
                    "addi r1, r1, %gen%"]
        # Write out value to special add
        get   = ["sw r0, 0(r1)"]
        # Add one to register
        next =  ["addi r0, r0, 1"]
        
        program = list(ListAssemble(reset, get, next).assemble())
        
        dut, out = core_with_program(program)
        
        async def process(ctx):
            for i in range(100):
                assert await get_gen(ctx, out) == i + 1
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(process)
        
        with sim.write_vcd("bench/ord_numbers.vcd") as vcd:
            sim.run()
            
    def test_multiples_three(self):
        # Clear registers
        # Set r1 to special address
        reset = ["andi r0, r0, 0", "andi r2, r2, 0",
                    "andi r3, r3, 0",
                    "addi r3, r3, 3", 
                    "andi r1, r1, 0",
                    "addi r1, r1, %gen%"]
        # Write out value to special add
        get   = ["sw r2, 0(r1)"]
        # Add one to register
        next =  ["addi r0, r0, 1", "mul r2, r0, r3"]
        
        program = list(ListAssemble(reset, get, next).assemble())
        
        dut, out = core_with_program(program)
        
        async def process(ctx):
            for i in range(100):
                assert await get_gen(ctx, out) == 3*i
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(process)
        
        with sim.write_vcd("bench/mul_three.vcd") as vcd:
            sim.run()
            
if __name__ == "__main__":
    unittest.main()