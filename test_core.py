import unittest
from amaranth.sim import *
from core.cpu import RiscCore
from interpret.exec import ExecProgram

from amaranth import Module
from amaranth.lib import wiring

from axi.axi_ram import AxiLiteMemory
from risc_build import RiscProject

async def get_tx(ctx, port, period):
    # Get start bit
    await ctx.tick().until(~port)
    await ctx.tick().repeat(period>>1)
    data = 0
    for i in range(8):
        result = await ctx.tick().sample(port).repeat(period)
        data = (data >> 1) + (result[0] << 7)
    return data
    

class Core(unittest.TestCase):
    def test_uart(self):
        program = [
            "andi x0, x0, 0",
            "addi x1, x0, 45",
            "sw x1, 10(x0)",
            "fence"
        ]
        
        ep = ExecProgram(program=program)
        
        m = Module()
        
        period = 4
        m.submodules.core = core = RiscProject(normally_on=True, uart_period=period)
        
        m.submodules.mem = mem = AxiLiteMemory(32, 256, init=list(ep.assemble()))
        
        wiring.connect(m, core.axi, mem.axi)
        
        async def process(ctx):
            ctx.set(core.rx, 1)
            result = await get_tx(ctx, core.tx, period)
            print(result)
            assert result == 45
            
        sim = Simulator(m)
        sim.add_clock(1e-8)
        sim.add_testbench(process)
        
        with sim.write_vcd("bench/test_uart_core.vcd") as vcd:
            sim.run()
        
        print("Ran uart test")
        
    def test_lw(self):
        program = [
            "andi x0, x0, 0",
            "addi x1, x0, 45",
            "addi x2, x0, 265", # Some place in ram
            "sw x1, 0(x2)", # Store 
            "lw x3, 0(x2)", # Load
            "sw x3, 10(x0)" # Write to uart
        ]
        
        ep = ExecProgram(program=program)
        
        m = Module()
        
        period = 4
        m.submodules.core = core = RiscProject(normally_on=True, uart_period=period)
        
        m.submodules.mem = mem = AxiLiteMemory(32, 256, init=list(ep.assemble()))
        
        wiring.connect(m, core.axi, mem.axi)
        
        async def process(ctx):
            ctx.set(core.rx, 1)
            result = await get_tx(ctx, core.tx, period)
            print(result)
            assert result == 45
            
        sim = Simulator(m)
        sim.add_clock(1e-8)
        sim.add_testbench(process)
        
        with sim.write_vcd("bench/test_lw_core.vcd") as vcd:
            sim.run()
        
        print("Ran uart test")
        
if __name__ == "__main__":
    unittest.main()