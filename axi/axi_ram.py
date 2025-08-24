from amaranth import *
from amaranth.lib import wiring, memory, enum, data
from amaranth.lib.wiring import In, Out

from infra.signature import AxiLite

class BusState(enum.Enum):
    IDLE = 0
    LOAD = 1
    DATA = 2
    RESP = 3

class AxiLiteMemory(wiring.Component):
    """
    Memory device for local core memory
    """
    def __init__(self, shape, depth, init = [], granularity = 2):
        self.shape = shape
        self.depth = depth
        self.init = init
        self.granularity = granularity
        
        super().__init__({
            "axi": In(AxiLite(32, shape))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        mem = m.submodules.mem = memory.Memory(shape=self.shape, 
                depth=self.depth,
                init=self.init)
        
        read_port = mem.read_port()
        write_port = mem.write_port()
        
        r_state = Signal(BusState)
        
        with m.Switch(r_state):
            with m.Case(BusState.IDLE):
                m.d.comb += self.axi.arready.eq(1)
                with m.If(self.axi.arready & self.axi.arvalid): 
                    m.d.sync += r_state.eq(BusState.LOAD)
                    m.d.sync += read_port.addr.eq(self.axi.araddr >> self.granularity)
            with m.Case(BusState.LOAD):
                m.d.comb += read_port.en.eq(1)
                m.d.sync += r_state.eq(BusState.DATA)
            with m.Case(BusState.DATA):
                m.d.comb += self.axi.rvalid.eq(1)
                m.d.comb += self.axi.rdata.eq(read_port.data)
                with m.If(self.axi.rvalid & self.axi.rready):
                    m.d.sync += r_state.eq(BusState.IDLE)
                    
        w_state = Signal(BusState)
        
        with m.Switch(w_state):
            with m.Case(BusState.IDLE):
                m.d.comb += self.axi.awready.eq(1)
                with m.If(self.axi.awready & self.axi.awvalid):
                    m.d.sync += w_state.eq(BusState.DATA)
                    m.d.sync += write_port.addr.eq(self.axi.awaddr >> self.granularity)
            with m.Case(BusState.DATA):
                m.d.comb += self.axi.wready.eq(1)
                with m.If(self.axi.wready & self.axi.wvalid):
                    m.d.sync += w_state.eq(BusState.LOAD)
                    m.d.sync += write_port.data.eq(self.axi.wdata)
            with m.Case(BusState.LOAD):
                m.d.comb += write_port.en.eq(1)
                m.d.sync += w_state.eq(BusState.RESP)
            with m.Case(BusState.RESP):
                m.d.comb += self.axi.bvalid.eq(1)
                m.d.comb += self.axi.bresp.eq(0)
                with m.If(self.axi.bvalid & self.axi.bready):
                    m.d.sync += w_state.eq(BusState.IDLE)
                
        return m