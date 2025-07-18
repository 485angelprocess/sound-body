import unittest
from amaranth.sim import *

from infra.switch import AddressSwitch
from infra.signature import Bus

class TestAddressSwitch(unittest.TestCase):
    def test_switch(self):
        """
        Test address switching for simple case
        """
        dut = AddressSwitch(split=256)
        
        # Write to switch
        async def write_process(ctx):
            await Bus.sim_write(ctx, dut.consume, 0, 10, sync=False)
            await Bus.sim_write(ctx, dut.consume, 256, 11, sync=False)
            await Bus.sim_write(ctx, dut.consume, 1, 12, sync=False)
            await Bus.sim_write(ctx, dut.consume, 257, 13, sync=False)
            
        # Get output of A
        async def a_process(ctx):
            assert await Bus.write_consume(ctx, dut.a, sync=False) == (0, 10)
            assert await Bus.write_consume(ctx, dut.a, sync=False) == (1, 12)
        
        # Get output of B
        async def b_process(ctx):
            assert await Bus.write_consume(ctx, dut.b, sync=False) == (0, 11)
            assert await Bus.write_consume(ctx, dut.b, sync=False) == (1, 13)
            
        sim = Simulator(dut)
        
        sim.add_testbench(write_process)
        sim.add_testbench(a_process)
        sim.add_testbench(b_process)
        
        with sim.write_vcd("bench/tb_address_switch.vcd"):
            sim.run()
            
if __name__ == "__main__":
    unittest.main()