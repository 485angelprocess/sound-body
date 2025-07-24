"""
Module for adding/subtracting
"""
from amaranth import *
from amaranth.lib import wiring, enum
from amaranth.lib.wiring import In, Out

class AluFunction(enum.Enum, shape=3):
    ADDSUB    = 0b000
    SHIFTLEFT = 0b001
    LESSTHAN  = 0b010
    LESSTHANU = 0b011
    XOR       = 0b100
    SHIFTRIGHT=0b101
    OR        =0b110
    AND       =0b111

# TODO make into more of a stream
class AluInputSignature(wiring.Signature):
    def __init__(self):
        super().__init__({
            "s1": In(32), # Value of first operator
            "s2": In(32), # Value of second operator
            "d": In(5),
            "function": In(AluFunction), # Function
            "mode": In(7),
            "valid": In(1)
        })
        
class AluOutputSignature(wiring.Signature):
    def __init__(self):
        super().__init__({
            "value": Out(32),
            "d": Out(5),
            "error": Out(1),
            "valid": Out(1)
        })

class Alu(wiring.Component):
    def __init__(self):
        super().__init__({
            "consume": Out(AluInputSignature()),
            "produce": Out(AluOutputSignature())
        })
        
    def elaborate(self, platform):
        m = Module()
        
        with m.If(self.produce.valid):
            m.d.sync += self.produce.valid.eq(0)
        
        with m.If(self.consume.valid):
            m.d.sync += self.produce.valid.eq(1)
            m.d.sync += self.produce.d.eq(self.consume.d)
        
            with m.Switch(self.consume.function):
                with m.Case(AluFunction.ADDSUB):
                    # Addition/subtraction
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            # ADD
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 + self.consume.s2
                            )
                        with m.Case(0b010_0000):
                            # SUB
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 - self.consume.s2
                            )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.SHIFTLEFT):
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            # Shift left
                            with m.If(self.consume.s2 > 5):
                                # Always 0
                                m.d.sync += self.produce.value.eq(0)
                            with m.Else():
                                # Shift is valid value
                                m.d.sync += self.produce.value.eq(
                                    self.consume.s1 <<
                                    self.consume.s2.as_unsigned()[0:3]
                                )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.LESSTHAN):
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            # Less than signed
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 <
                                self.consume.s2
                            )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.LESSTHANU):
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                             # Less than unsigned
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1.as_unsigned() <
                                self.consume.s2.as_unsigned()
                            )      
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.XOR):
                    # Exclusive or
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 ^
                                self.consume.s2
                            )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.SHIFTRIGHT):
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            # Logical shift right
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 >> self.consume.s2
                            )
                        with m.Case(0b010_0000):
                            # Arithmetic shift right
                            m.d.sync += self.produce.value[0:31].eq(
                                self.consume.s1 >>
                                self.consume.s2.as_unsigned()
                            )
                            m.d.sync += self.produce.value[-1].eq(
                                self.consume.s1[-1]
                            )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.OR):
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 |
                                self.consume.s2
                            )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                with m.Case(AluFunction.AND):
                    with m.Switch(self.consume.mode):
                        with m.Case(0b000_0000):
                            m.d.sync += self.produce.value.eq(
                                self.consume.s1 &
                                self.consume.s2
                            )
                        with m.Default():
                            m.d.sync += self.produce.error.eq(1)
                
        return m