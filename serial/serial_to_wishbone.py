"""
Get serial stream
"""
from amaranth import *
from amaranth.lib import wiring, enum
from amaranth.lib.wiring import In, Out

from signature import Bus, Stream

class SerialCommand(object):
    WRITE_SHORT = 'w'
    WRITE_LONG = 'W'
    READ_SHORT = 'r'
    READ_LONG  = 'R'

class SerialToWishbone(wiring.Component):
    def __init__(self):
        super().__init__({
            "command": In(Stream(8)), # Serial stream
            "reply": Out(Stream(8)),
            "produce": Out(Bus(32, 32))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        size = Signal(2)
        counter = Signal(2)
        
        prefix = Signal(8)
        arg = Signal(32)
        
        with m.FSM():
            with m.State("Idle"):
                m.d.comb += self.command.tready.eq(1)
                m.d.sync += self.produce.addr.eq(0)
                m.d.sync += self.produce.w_data.eq(0)
                m.d.sync += self.produce.w_en.eq(0)
                
                with m.If(self.command.tvalid):
                    with m.Switch(self.command.tdata):
                        with m.Case(ord(SerialCommand.WRITE_SHORT)):
                            m.d.sync += self.produce.w_en.eq(1)
                            m.d.sync += size.eq(0)
                            m.d.sync += counter.eq(0)
                            m.next = "Address"
                        with m.Case(ord(SerialCommand.WRITE_LONG)):
                            m.d.sync += self.produce.w_en.eq(1)
                            m.d.sync += size.eq(3)
                            m.d.sync += counter.eq(3)
                            m.next = "Address"
                        with m.Case(ord(SerialCommand.READ_SHORT)):
                            m.d.sync += size.eq(0)
                            m.d.sync += counter.eq(0)
                            m.next = "Address"
                        with m.Case(ord(SerialCommand.READ_LONG)):
                            m.d.sync += size.eq(3)
                            m.d.sync += counter.eq(3)
                            m.next = "Address"
                        with m.Case(ord('\n')):
                            m.next = "EOL"
                        with m.Default():
                            m.d.sync += prefix.eq(ord('%'))
                            m.d.sync += arg.eq(self.command.tdata)
                            m.next = "Print"
            ################################
            ### Write/read to bus ##########
            ################################
            with m.State("Address"):
                m.d.comb += self.command.tready.eq(1)
                with m.If(self.command.tvalid):
                    m.d.sync += self.produce.addr.word_select(counter, 8).eq(self.command.tdata)
                    with m.If(counter == 0):
                        m.d.sync += counter.eq(size)
                        with m.If(self.produce.w_en):
                            m.next = "Data"
                        with m.Else():
                            m.next = "Bus"
                    with m.Else():
                        m.d.sync += counter.eq(counter - 1)
            with m.State("Data"):
                m.d.comb += self.command.tready.eq(1)
                with m.If(self.command.tvalid):
                    m.d.sync += self.produce.w_data.word_select(counter, 8).eq(self.command.tdata)
                    with m.If(counter == 0):
                        m.next = "Bus"
                    with m.Else():
                        m.d.sync += counter.eq(counter - 1)
                        
            with m.State("Bus"):
                # Write to bus
                m.d.comb += self.produce.stb.eq(1)
                m.d.comb += self.produce.cyc.eq(1)
                with m.If(self.produce.ack):
                    with m.If(self.produce.w_en):
                        m.d.sync += prefix.eq(ord('W'))
                        m.d.sync += arg.eq(1)
                    with m.Else():
                        m.d.sync += prefix.eq(ord('R'))
                        m.d.sync += arg.eq(self.produce.r_data)
                    m.next = "Print"
            
            ################################
            ## Print reply #################
            ################################
            with m.State("Print"):
                m.d.comb += self.reply.tvalid.eq(1)
                m.d.comb += self.reply.tdata.eq(prefix)
                with m.If(self.reply.tready):
                    m.d.sync += counter.eq(3)
                    m.next = "PrintArg"
            with m.State("PrintArg"):
                m.d.comb += self.reply.tvalid.eq(1)
                m.d.comb += self.reply.tdata.eq(arg[24:32]) # Print MSB first
                
                with m.If(self.reply.tready):
                    m.d.sync += arg.eq(arg << 8) # Shift up prefix
                    with m.If(counter == 0):
                        m.next = "EOL"
                    with m.Else():
                        m.d.sync += counter.eq(counter - 1)
            ######################################
            ### print new line ###################
            ######################################
            with m.State("EOL"):
                m.d.comb += self.reply.tvalid.eq(1)
                m.d.comb += self.reply.tdata.eq(ord('\n'))
                with m.If(self.reply.tready):
                    m.next = "Idle"
            
        
        return m