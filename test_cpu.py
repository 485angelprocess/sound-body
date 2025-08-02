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
    
async def check_addr(ctx, port, addr, data):
    result = await Bus.write_consume(ctx,port)
    assert result[0] == addr
    assert result[1] == data

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
        
        finished = [False]
        async def expect(ctx):
            result = await Bus.write_consume(ctx,bus)
            assert result[0] == 0
            assert result[1] == 3
            finished[0] = True
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(expect)
        
        
        with sim.write_vcd("bench/test_addi.vcd") as vcd:
            sim.run()
            
        assert finished[0] == True
            
    def test_lui(self):
        
        value = 113
        expected_value = value << 12
        
        program = [
            "lui r0, {}".format(value),
            "andi r1, r1, 0",
            "addi r0, r0, 3",
            "sw r0, 0(r1)"
        ]
        
        ep = ExecProgram(program=program)
        dut, bus = core_with_program(list(ep.assemble()))
        
        finished = [False]
        async def expect(ctx):
            result = await Bus.write_consume(ctx,bus)
            print("Got result {}".format(result))
            print("Expected {}".format(expected_value))
            assert result[0] == 0
            assert result[1] == expected_value
            finished[0] = True
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(expect)
        
        with sim.write_vcd("bench/test_lui.vcd") as vcd:
            sim.run_until(100*1e-8)
            
        assert finished[0] == True
            
    def test_jal(self):
        program = [
            "andi r0, r0, 0",
            "jal  r1, 8(r0)",
            "addi r0, r0, 11",
            "addi r0, r0, 13",
            "andi r2, r2, 0",
            "sw r0, 0(r2)",
            "sw r1, 4(r2)"
        ]
        
        ep = ExecProgram(program=program)
        dut, bus = core_with_program(list(ep.assemble()))
        
        finished = [False]
        async def expect(ctx):
            await check_addr(ctx, bus, 0, 13)
            await check_addr(ctx, bus, 4, 8)
            finished[0] = True
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(expect)
        
        with sim.write_vcd("bench/test_jal.vcd") as vcd:
            sim.run_until(100*1e-8)
        
        assert finished[0] == True
        
    def test_jalr(self):
        program = [
            "andi r0, r0, 0",
            "jalr r1, r0, 12",
            "addi r0, r0, 11",
            "addi r0, r0, 15",
            "andi r2, r2, 0",
            "sw r0, 0(r2)",
            "sw r1, 4(r2)"
        ]
        
        ep = ExecProgram(program=program)
        dut, bus = core_with_program(list(ep.assemble()))
        
        finished = [False]
        async def expect(ctx):
            await check_addr(ctx, bus, 0, 15)
            await check_addr(ctx, bus, 4, 8)
            finished[0] = True
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(expect)
        
        with sim.write_vcd("bench/test_jalr.vcd") as vcd:
            sim.run_until(100*1e-8)
        
        assert finished[0] == True
        
if __name__ == "__main__":
    unittest.main()