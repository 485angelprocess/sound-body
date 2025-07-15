"""
Axi script
"""
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from infra.signature import AxiLite

class AxiCommand(object):
    def __init__(self, address, data):
        self.address = address
        self.data = data
        
class AxiScript(wiring.Component):
    """
    Send a script of axi commands to a modiule
    """
    def __init__(self, *commands, address_shape = 8, data_shape = 32):
        self.commands = list(commands)
        
        self.address_shape = address_shape
        self.data_shape = data_shape
        
        super().__init__({
            "ctl": Out(AxiLite(address_shape, data_shape))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        counter = Signal(range(len(self.commands) + 1))
        
        with m.If(self.ctl.bvalid & self.ctl.bready):
            m.d.sync += self.ctl.bready.eq(0)

        with m.FSM():
            with m.State("Idle"):
                with m.If(counter < len(self.commands)):
                    m.next = "Addr"
            with m.State("Addr"):
                with m.Switch(counter):
                    for i in range(len(self.commands)):
                        with m.Case(i):
                            m.d.comb += self.ctl.awaddr.eq(self.commands[i].address)
                m.d.comb += self.ctl.awvalid.eq(1)
                with m.If(self.ctl.awready):
                    m.next = "Data"
            with m.State("Data"):
                with m.Switch(counter):
                    for i in range(len(self.commands)):
                        with m.Case(i):
                            m.d.comb += self.ctl.wdata.eq(self.commands[i].data)
                m.d.comb += self.ctl.wvalid.eq(1)
                with m.If(self.ctl.wready):
                    m.d.sync += self.ctl.bready.eq(1)
                    m.d.sync += counter.eq(counter + 1)
                    m.next = "Idle"
                        
        return m