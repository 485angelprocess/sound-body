"""
UART drivcer
"""
from amaranth import *
from amaranth.lib import wiring, fifo
from amaranth.lib.wiring import In, Out

from infra.signature import Bus, Stream

class UartTx(wiring.Component):
    def __init__(self, period = 10417, parity = False, stop = 2):
        self.period = period
        self.parity = parity
        self.stop = stop
    
        super().__init__({
            "consume": In(Stream(8)),
            "tx": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        buffer = m.submodules.buffer = fifo.SyncFIFO(width = 8, depth = 4)
        
        m.d.comb += [
            buffer.w_en.eq(self.consume.tvalid),
            buffer.w_data.eq(self.consume.tdata),
            self.consume.tready.eq(buffer.w_rdy)
        ]
        
        data_register = Signal(8)
        parity = Signal()
        
        counter = Signal(range(self.period))
        byte_counter = Signal(3)
        
        with m.FSM():
            with m.State("Idle"):
                # Wait for data
                m.d.comb += self.tx.eq(1)
                with m.If(buffer.r_rdy):
                    m.d.comb += buffer.r_en.eq(1)
                    m.d.sync += data_register.eq(buffer.r_data)
                    m.d.sync += counter.eq(self.period - 1)
                    m.next = "Start"
            with m.State("Start"):
                # Send start bit
                m.d.comb += self.tx.eq(0)
                with m.If(counter == 0):
                    m.d.sync += counter.eq(self.period - 1)
                    m.d.sync += byte_counter.eq(7)
                    m.next = "Data"
                with m.Else():
                    m.d.sync += counter.eq(counter - 1)
            with m.State("Data"):
                # Shift out data
                m.d.comb += self.tx.eq(data_register[0])
                with m.If(counter == 0):
                    m.d.sync += parity.eq(parity + data_register[0])
                    m.d.sync += data_register.eq(data_register >> 1)
                    m.d.sync += counter.eq(self.period - 1)
                    with m.If(byte_counter == 0):
                        if self.parity:
                            m.next = "Parity"
                        else:
                            m.d.sync += byte_counter.eq(self.stop - 1)
                            m.next = "Stop"
                    with m.Else():
                        m.d.sync += byte_counter.eq(byte_counter - 1)
                with m.Else():
                    m.d.sync += counter.eq(counter - 1)
            with m.State("Parity"):
                # Shift out parity bit
                m.d.comb += self.tx.eq(parity)
                with m.If(counter == 0):
                    m.d.sync += parity.eq(0)
                    m.d.sync += byte_counter.eq(self.stop - 1)
                    m.d.sync += counter.eq(self.period - 1)
                    m.next = "Stop"
                with m.Else():
                    m.d.sync += counter.eq(counter - 1)
            with m.State("Stop"):
                # Send stop bits
                m.d.comb += self.tx.eq(1)
                with m.If(counter == 0):
                    with m.If(byte_counter == 0):
                        m.next = "Idle"
                    with m.Else():
                        m.d.sync += byte_counter.eq(byte_counter - 1)
                        m.d.sync += counter.eq(self.period - 1)
                with m.Else():
                    m.d.sync += counter.eq(counter - 1)
        
        return m
        
class UartRx(wiring.Component):
    def __init__(self, period = 10417, parity = False, stop = 1, depth = 4):
        self.period = period
        self.parity = parity
        self.stop = stop
        self.depth = depth
        super().__init__({
            "produce": Out(Stream(8)),
            "rx": In(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        buffer = m.submodules.buffer = fifo.SyncFIFO(width = 8, depth = self.depth)
        
        m.d.comb += [
            self.produce.tdata.eq(buffer.r_data),
            self.produce.tvalid.eq(buffer.r_rdy),
            buffer.r_en.eq(self.produce.tready)
        ]
        
        counter = Signal(range(self.period))
        
        with m.If(counter > 0):
            m.d.sync += counter.eq(counter - 1)
            
        bit_counter = Signal(3)
        data_register = Signal(8)
        
        with m.FSM():
            with m.State("Idle"):
                with m.If(self.rx == 0):
                    # Probably start bit
                    m.d.sync += counter.eq(self.period >> 1) # half period
                    m.next = "Start"
            with m.State("Start"):
                with m.If(counter == 0):
                    with m.If(self.rx == 1):
                        # False start
                        m.next = "Idle"
                    with m.Else():
                        m.d.sync += bit_counter.eq(7)
                        m.d.sync += counter.eq(self.period - 1)
                        m.next = "Data"
            with m.State("Data"):
                with m.If(counter == 0):
                    m.d.sync += data_register.eq((data_register >> 1) + (self.rx << 7))
                    m.d.sync += counter.eq(self.period - 1)
                    with m.If(bit_counter == 0):
                        if self.parity:
                            m.next = "Parity"
                        else:
                            m.d.sync += bit_counter.eq(self.stop - 1)
                            m.next = "Stop"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)
            with m.State("Parity"):
                with m.If(counter == 0):
                    m.d.sync += counter.eq(self.period - 1)
                    m.d.sync += bit_counter.eq(self.stop - 1)
                    m.next = "Stop"
            with m.State("Stop"):
                with m.If(counter == 0):
                    with m.If(bit_counter == 0):
                        m.d.comb += buffer.w_data.eq(data_register)
                        m.d.comb += buffer.w_en.eq(1)
                        m.next = "Idle"
                    with m.Else():
                        m.d.sync += counter.eq(self.period - 1)
                        m.d.sync += bit_counter.eq(bit_counter - 1)
                
                        
                        
        
        return m