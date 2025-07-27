"""
Get serial stream
"""
from amaranth import *
from amaranth.lib import wiring, enum
from amaranth.lib.wiring import In, Out

from infra.signature import Bus, Stream

class SerialCommand(object):
    WRITE_SHORT = 'w'
    WRITE_LONG = 'W'
    READ_SHORT = 'r'
    READ_LONG  = 'R'
    ECHO = 'e'
    ID = 'I'
    RESET = 'x'
    
class UartRegister(object):
    TX = 0

class SerialToWishbone(wiring.Component):
    def __init__(self):
        super().__init__({
            "command": In(Stream(8)), # Serial stream
            "reply": Out(Stream(8)),
            "produce": Out(Bus(32, 32)),
            "bus": In(Bus(32, 8)),
            "soft_reset": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        size = Signal(2)
        counter = Signal(3)
        
        prefix = Signal(8)
        arg = Signal(64)
        
        ext_reset = Signal(reset = 1)
        
        m.d.comb += self.soft_reset.eq(ext_reset)
        
        timer = Signal(32)
        
        timeout = 100_000_000
        
        with m.FSM() as fsm:
            # From external computer
            with m.State("Idle"):
                m.d.comb += self.command.ready.eq(1)
                m.d.sync += self.produce.addr.eq(0)
                m.d.sync += self.produce.w_data.eq(0)
                m.d.sync += self.produce.w_en.eq(0)
                m.d.sync += timer.eq(0)
                with m.If(self.command.valid):
                    with m.Switch(self.command.data):
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
                        with m.Case(ord(SerialCommand.ID)):
                            m.d.sync += prefix.eq(ord("I"))
                            m.d.sync += arg.eq(ord("D"))
                            m.d.sync += counter.eq(0)
                            m.next = "Print"
                        with m.Case(ord(SerialCommand.ECHO)):
                            m.next = "Echo"
                        with m.Case(ord('\n')):
                            m.next = "EOL"
                        with m.Case(ord(SerialCommand.RESET)):
                            m.d.sync += ext_reset.eq(0)
                        with m.Default():
                            m.d.sync += prefix.eq(ord('%'))
                            m.d.sync += arg.eq(self.command.data)
                            m.d.sync += counter.eq(0)
                            m.next = "Print"
            ################################
            ### Write/read to bus ##########
            ################################
            with m.State("Address"):
                m.d.comb += self.command.ready.eq(1)
                with m.If(self.command.valid):
                    m.d.sync += self.produce.addr.word_select(counter, 8).eq(self.command.data)
                    with m.If(counter == 0):
                        m.d.sync += counter.eq(size)
                        with m.If(self.produce.w_en):
                            m.next = "Data"
                        with m.Else():
                            m.next = "Bus"
                    with m.Else():
                        m.d.sync += counter.eq(counter - 1)
            with m.State("Data"):
                m.d.comb += self.command.ready.eq(1)
                with m.If(self.command.valid):
                    m.d.sync += self.produce.w_data.word_select(counter, 8).eq(self.command.data)
                    with m.If(counter == 0):
                        m.next = "Bus"
                    with m.Else():
                        m.d.sync += counter.eq(counter - 1)
                        
            with m.State("Bus"):
                with m.If(timer == timeout):
                    m.d.sync += prefix.eq(ord('T'))
                    m.d.sync += arg.eq(self.produce.addr)
                    m.d.sync += counter.eq(3)
                    m.next = "Print"
                with m.Else():
                    m.d.sync += timer.eq(timer + 1)
            
                # Write to bus
                m.d.comb += self.produce.stb.eq(1)
                m.d.comb += self.produce.cyc.eq(1)
                with m.If(self.produce.ack):
                    with m.If(self.produce.w_en):
                        m.d.sync += self.produce.w_en.eq(0)
                        m.d.sync += counter.eq(7)
                        m.d.sync += prefix.eq(ord('W'))
                        m.d.sync += arg[0:32].eq(self.produce.w_data)
                        m.d.sync += arg[32:64].eq(self.produce.addr)
                    with m.Else():
                        m.d.sync += prefix.eq(ord('R'))
                        m.d.sync += counter.eq(7)
                        m.d.sync += arg[0:32].eq(self.produce.r_data)
                        m.d.sync += arg[32:64].eq(self.produce.addr)
                    m.next = "Print"
            
            ################################
            ## Print reply #################
            ################################
            with m.State("Print"):
                m.d.comb += self.reply.valid.eq(1)
                m.d.comb += self.reply.data.eq(prefix)
                with m.If(self.reply.ready):
                    m.next = "PrintArg"
            with m.State("PrintArg"):
                m.d.comb += self.reply.valid.eq(1)
                m.d.comb += self.reply.data.eq(arg.word_select(counter, 8)) # Print MSB first
                
                with m.If(self.reply.ready):
                    with m.If(counter == 0):
                        m.next = "Idle"
                    with m.Else():
                        m.d.sync += counter.eq(counter - 1)
            ######################################
            ### print new line ###################
            ######################################
            with m.State("EOL"):
                m.d.comb += self.reply.valid.eq(1)
                m.d.comb += self.reply.data.eq(ord('\n'))
                with m.If(self.reply.ready):
                    m.next = "Idle"
                    
            with m.State("Echo"):
                # Echo one byte
                m.d.comb += self.reply.valid.eq(self.command.valid)
                m.d.comb += self.reply.data.eq(self.command.data)
                m.d.comb += self.command.ready.eq(self.reply.ready)
                
                with m.If(self.reply.valid & self.reply.ready):
                    m.next = "Idle"

        with m.If(fsm.ongoing("Idle") & (~self.command.valid)):
            # Control from CPU
            with m.If(self.bus.stb & self.bus.cyc & self.bus.w_en):
                m.d.comb += self.reply.valid.eq(1) # Send reply
                m.d.comb += self.bus.ack.eq(self.reply.ready)
                m.d.comb += self.reply.data.eq(self.bus.w_data)
            
        return m