"""
Square wave generator
"""
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from infra.signature import Stream

class SquareGenerator(wiring.Component):
    def __init__(self, period = 100, amplitude = 500):
        self.period = period << 1
        self.amplitude = amplitude
        
        super().__init__({
            "produce": Out(Stream(32, tid = Out(3)))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        counter = Signal(range(self.period))
        
        with m.If(counter < self.period >> 1):
            m.d.comb += self.produce.tdata.eq(self.amplitude)
        with m.Else():
            m.d.comb += self.produce.tdata.eq(0)
            
        m.d.comb += self.produce.tvalid.eq(1)
        
        with m.If(self.produce.tvalid & self.produce.tready):
            with m.If(counter == self.period - 1):
                m.d.sync += counter.eq(0)
            with m.Else():
                m.d.sync += counter.eq(counter + 1)
                
        m.d.comb += self.produce.tid.eq(counter[0])
        
        return m