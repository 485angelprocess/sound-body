from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from infra.signature import Stream

class Buffer(wiring.Component):
    """
    Full throughput buffer
    """
    def __init__(self, shape):
        self.shape = shape
        super().__init__({
            "consume": In(Stream(shape)),
            "produce": Out(Stream(shape))
        })
        
    @classmethod
    def from_port(cls, m, port, name):
        shape = port.signature.members["data"].shape
        
        b = cls(shape)
        
        m.submodules["{}_buffer".format(name)] = b
        
        m.d.comb += [
            b.consume.data.eq(port.data),
            b.consume.valid.eq(port.valid),
            port.ready.eq(b.consume.ready)
        ]
        
        return b
        
    def elaborate(self, platform):
        m = Module()
        
        cache = Array([Signal(self.shape, name="c{}".format(i)) for i in range(2)])
        cache_ready = Signal(2, reset=0b11)
        select = Signal()
        produce_select = Signal()
        
        m.d.comb += produce_select.eq(select + 1)
        
        m.d.comb += self.produce.data.eq(cache[produce_select])
        
        with m.Switch(select):
            with m.Case(0):
                m.d.comb += self.consume.ready.eq(cache_ready[0])
                m.d.comb += self.produce.valid.eq(~cache_ready[1])
            with m.Case(1):
                m.d.comb += self.consume.ready.eq(cache_ready[1])
                m.d.comb += self.produce.valid.eq(~cache_ready[0])
        
        with m.If(self.consume.ready & self.consume.valid):
            m.d.sync += cache[select].eq(self.consume.data)
            m.d.sync += select.eq(select + 1)
            # Clear ready bit
            m.d.sync += cache_ready.bit_select(select, 1).eq(0)
            
        with m.If(self.produce.ready & self.produce.valid):
            # Set ready bit
            m.d.sync += cache_ready.bit_select(produce_select, 1).eq(1)
            
        return m
        
