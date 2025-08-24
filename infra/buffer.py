from amaranth import *
from amaranth.lib import wiring, fifo
from amaranth.lib.wiring import In, Out
from infra.signature import Stream

class Buffer(wiring.Component):
    """
    Buffer
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
        
        width = None
        if hasattr(self.shape, "size"):
            width = self.shape.size
        else:
            width = self.shape.width
        
        m.submodules.mfifo = mfifo = fifo.SyncFIFO(width=width,depth=2)
        
        m.d.comb += [
            mfifo.w_data.eq(self.consume.data),
            mfifo.w_en.eq(self.consume.valid),
            self.consume.ready.eq(mfifo.w_rdy)
        ]
        
        m.d.comb += [
            self.produce.data.eq(mfifo.r_data),
            self.produce.valid.eq(mfifo.r_rdy),
            mfifo.r_en.eq(self.produce.ready)
        ]
            
        return m
        
