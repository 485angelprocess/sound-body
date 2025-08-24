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

from axi.axi_ram import AxiLiteMemory
from risc_build import RiscProject

class ExpectedWrite(object):
    def __init__(self, addr, data, size=2):
        self.addr = addr
        self.data = data
        self.size = size

def test_program(name, program, *expected_value):
    ep = ExecProgram(program=program)
    dut, bus = core_with_program(list(ep.assemble()))
    
    finished = [False]
    async def expect(ctx):
        for ex in expected_value:
            # TODO add size component
            result = await Bus.write_consume(ctx,bus)
            try:
                assert result[0] == ex.addr
                print("Got data {}", ex.data)
                assert result[1] == ex.data
            except AssertionError as e:
                print("Got address {}, Data: {}".format(result[0], result[1]))
                print("Expected {}: {}".format(ex.addr, ex.data))
                raise e
        finished[0] = True
        
    sim = Simulator(dut)
    sim.add_clock(1e-8)
    sim.add_testbench(expect)
    
    with sim.write_vcd("bench/test_{}.vcd".format(name)) as vcd:
        sim.run_until(100*1e-8)
        
    assert finished[0] == True


def core_with_program(program):
    dut = Module()
    
    #print("Loading program: ")
    #for i in range(len(program)):
    #    print("\t{:02X}: {:02X}".format(i, program[i]))
    
    dut.submodules.cpu = cpu = RiscCore(has_mul=False, normally_on=True)
    dut.submodules.ram = ram = WishboneMemory(32, 512, init=program, granularity=2)
    
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
            "jal  r1, 8",
            "addi r0, r0, 11",
            "addi r0, r0, 13",
            "andi r2, r2, 0",
            "sw r0, 0(r2)",
            "sw r1, 4(r2)"
        ]
        
        test_program("jal", program, ExpectedWrite(0, 13), ExpectedWrite(4, 8))
        
    def test_jalr(self):
        program = [
            "andi r0, r0, 0",
            "jalr r1, 12(r0)",
            "addi r0, r0, 11",
            "addi r0, r0, 15",
            "andi r2, r2, 0",
            "sw r0, 0(r2)",
            "sw r1, 4(r2)"
        ]
        
        test_program("jalr", program, ExpectedWrite(0, 15), ExpectedWrite(4, 8))
        
    def test_auipc(self):
        value = 15
        expected_value = (value << 12) + 4
        
        program = [
            "andi x3, x3, 0",
            "auipc x3, 15",
            "andi x0, x0, 0",
            "sw x3, 0(x0)"
        ]
        
        test_program("auipc", program, ExpectedWrite(0, expected_value))
        
    def test_slti(self):
        program = [
            "andi x3, x3, 0",
            "addi x3, x3, 5",
            "slti x4, x3, 6",
            "sw x4, 0(x0)",
            "slti x4, x3, 4",
            "sw x4, 0(x0)"
        ]
        
        test_program("slti", program, ExpectedWrite(0, 1), ExpectedWrite(0, 0))
        
    def test_xori(self):
        program = [
            "andi x3, x3, 0",
            "addi x3, x3, 15",
            "xori x4, x3, 11",
            "sw x4, 0(x0)"
        ]
        
        test_program("xori", program, ExpectedWrite(0, 4))
        
    def test_ori(self):
        program = [
            "andi x3, x3, 0",
            "addi x3, x3, 35",
            "ori x4, x3, 15",
            "sw x4, 0(x0)"
        ]
        
        test_program("ori", program, ExpectedWrite(0, 47))
        
    def test_slli(self):
        program = [
            "andi x3, x3, 0",
            "addi x3, x3, 12",
            "slli x4, x3, 2",
            "sw x4, 0(x0)"
        ]
        
        test_program("slli", program, ExpectedWrite(0, 48))
        
    def test_srli(self):
        program = [
            "andi x3, x3, 0",
            "addi x3, x3, 15",
            "srli x4, x3, 1",
            "sw x4, 0(x0)"
        ]
        
        test_program("srli", program, ExpectedWrite(0, 7))
        
    def test_add(self):
        program = [
            "addi x3, x0, 15",
            "addi x4, x0, 17",
            "add x5, x4, x3",
            "sw x5, 4(x0)"
        ]
        
        test_program("add", program, ExpectedWrite(4, 32))
        
    def test_sub(self):
        program = [
            "addi x3, x0, 34",
            "addi x4, x0, 12",
            "sub x5, x4, x3",
            "sw x5, 0(x0)"
        ]
        
        test_program("sub", program, ExpectedWrite(0, -22))
        
    def test_sll(self):
        program = [
            "addi x3, x0, 10",
            "addi x4, x0, 2",
            "sll x5, x3, x4",
            "sw x5, 0(x0)"
        ]
        
        test_program("sll", program, ExpectedWrite(0, 40))
        
    def test_slt(self):
        program = [
            "addi x3, x0, 15",
            "addi x4, x0, 2",
            "slt x5, x4, x3",
            "slt x6, x3, x4",
            "sw x5, 0(x0)",
            "sw x6, 0(x0)"
        ]
        
        test_program("slt", program,
                ExpectedWrite(0, 1),
                ExpectedWrite(0, 0))
                
    def test_xor(self):
        program = [
            "addi x3, x0, 15",
            "addi x4, x0, 75",
            "xor x5, x4, x3",
            "sw x5, 0(x0)"
        ]
        
        test_program("xor", program, ExpectedWrite(0, 68))
        
    def test_fence(self):
        # This tests that fence is? 
        # thread breakpoint
        # store and write orders are unimportant
        program = [
            "addi x2, x0, 11",
            "addi x3, x0, 13",
            "sw x2, 0(x0)",
            "sw x3, 4(x0)",
            "fence",
            "sw x3, 8(x0)"
        ]
        
        test_program("fence", program, 
                ExpectedWrite(0, 11),
                ExpectedWrite(4, 13))
        
    def test_basic(self):
        program = [
            "jalr x5, 256(x0)"
        ]
        program += ["noop"] * (63)
        program += [
            "lui x6, 1",
            "andi x0, x0, 0",
            "sw x6, 0(x0)"
        ]
        
        test_program("basic_kernel", program, ExpectedWrite(0, 4096))
        


if __name__ == "__main__":
    unittest.main()