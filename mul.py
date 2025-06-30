from amaranth import *
from amaranth.lib import wiring, enum, data
from amaranth.lib.wiring import In, Out

class MulSignature(wiring.Signature):
    def __init__(self):
        super().__init__({
            "muldiv": In(1),
            "f": In(3),
            "a": In(signed(32)), # source values
            "b": In(signed(32)),
            "en": In(1),
            "result": Out(32),
            "done": Out(1)
        })
    
class MulUnit(wiring.Component):
    def __init__(self):
        super().__init__({
            "bus": Out(MulSignature())
        })
    
    def elaborate(self, platform):
        m = Module()
        
        working = Signal(64)
        
        m.d.sync += self.bus.done.eq(0)
        
        # Multiply
        with m.Switch(self.bus.f):
            with m.Case(0b000):
                # Multiply and get lower 32
                m.d.comb += self.bus.result.eq(working[0:32])
                with m.If(self.bus.en):
                    m.d.sync += working.eq(self.bus.a * self.bus.b)
                    m.d.sync += self.bus.done.eq(1)
            with m.Case(0b001):
                # Multiply and get upper 32
                m.d.comb += self.bus.result.eq(working[32:64])
                with m.If(self.bus.en):
                    m.d.sync += working.eq(self.bus.a * self.bus.b)
                    m.d.sync += self.bus.done.eq(1)
            with m.Case(0b010):
                # Multiply signed rs1 by signed rs2
                m.d.comb += self.bus.result.eq(working[32:])
                with m.If(self.bus.en):
                    m.d.sync += working.eq(self.bus.a * self.bus.b.as_unsigned())
                    m.d.sync += self.bus.done.eq(1)
            with m.Case(0b010):
                # Multiply signed rs1 by signed rs2
                m.d.comb += self.bus.result.eq(working[32:])
                with m.If(self.bus.en):
                    m.d.sync += working.eq(self.bus.a.as_unsigned() * self.bus.b.as_unsigned())
                    m.d.sync += self.bus.done.eq(1)
            with m.Default():
                # Divide
                m.d.sync += Assert(0, "Division not implemented")
        
        return m