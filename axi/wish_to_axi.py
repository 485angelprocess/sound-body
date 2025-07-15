"""
Wishbone to AXI-4
"""
from infra import signature
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

class WishboneToAxi(wiring.Component):
    """
    Wishbone bus to axi lite
    """
    def __init__(self, ain = 32, din = 32, aout = 32, dout = 32):
        super().__init__({
            "wish": In(signature.Bus(ain, din)),
            "axi": Out(signature.AxiLite(aout, dout))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        address_written = Signal()
        
        # Write
        m.d.comb += self.axi.awvalid.eq(self.wish.w_en & self.wish.stb & self.wish.cyc & (~address_written))
        m.d.comb += self.axi.wvalid.eq(self.wish.w_en & self.wish.stb & self.wish.cyc & (address_written))
        
        # Read
        m.d.comb += self.axi.arvalid.eq((~self.wish.w_en) & self.wish.stb & self.wish.cyc & (~address_written))
        m.d.comb += self.axi.rready.eq((~self.wish.w_en) & self.wish.stb & self.wish.cyc & (
            address_written
        ))
        
        # Get response
        with m.If(self.wish.w_en):
            m.d.comb += self.wish.ack.eq(self.axi.wready & self.axi.wvalid)
        with m.Else():
            m.d.comb += self.wish.ack.eq(self.axi.rready & self.axi.rvalid)
        
        
        # Address written, set flag
        with m.If(self.axi.awvalid & self.axi.awready):
            m.d.sync += address_written.eq(1)
        with m.If(self.axi.arvalid & self.axi.arready):
            m.d.sync += address_written.eq(1)
            
        # Finished read
        with m.If(self.axi.rvalid & self.axi.rready):
            m.d.sync += address_written.eq(0)
        
        # Finished write and get response
        with m.If(self.axi.wvalid & self.axi.wready):
            m.d.sync += self.axi.bready.eq(1)
            
        with m.If(self.axi.bready & self.axi.bvalid):
            m.d.sync += self.axi.bready.eq(0)
            m.d.sync += address_written.eq(0)
            
        
        return m