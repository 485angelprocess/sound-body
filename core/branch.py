"""
Branch device
"""
from amaranth import *
from amaranth.lib import wiring, data
from amaranth.lib.wiring import In, Out

branch_shape = data.StructLayout({
    "f": 3,
    "a": signed(32),
    "b": signed(32),
})

class BranchDevice(wiring.Component):
    """
    Gives a signal if a branch should be taken
    """
    def __init__(self):
        super().__init__({
            "en": In(1),
            "consume": In(branch_shape),
            "branch": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        function = self.consume.f
        a = self.consume.a
        b = self.consume.b
        
        with m.If(self.en):
            with m.Switch(function):
                with m.Case(0b000):
                    # Barnch if equal
                    m.d.comb += self.branch.eq(
                        a == b
                    )
                with m.Case(0b001):
                    # Branch not equal
                    m.d.comb += self.branch.eq(
                        a != b
                    )
                with m.Case(0b100):
                    # Branch less than
                    m.d.comb += self.branch.eq(
                        a < b
                    )
                with m.Case(0b101):
                    # Branch greater than
                    m.d.comb += self.branch.eq(
                        a >= b
                    )
                with m.Case(0b110):
                    # Branch less than unsigned
                    m.d.comb += self.branch.eq(
                        a.as_unsigned() < b.as_unsigned()
                    )
                with m.Case(0b111):
                    # Branch greater than equal unsigned
                    m.d.comb += self.branch.eq(
                        a.as_unsigned() >= b.as_unsigned()
                    )
                with m.Default():
                    # Undefined branch functin
                    pass 
        
        return m