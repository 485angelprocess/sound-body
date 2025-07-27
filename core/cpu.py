"""
Implementation of RV32I instructions
"""
from amaranth import *
from amaranth.lib import wiring, enum, data
from amaranth.lib.wiring import In, Out
from infra.signature import Bus

from infra.buffer import Buffer

from core.mul import MulSignature, MulUnit

from core.alu import Alu, AluInputSignature, AluOutputSignature
from core.decode import InstructionDecode
from core.shape import Instruction, write_shape, decode_shape

class WriteRoute(enum.Enum):
    NONE= 0
    ALU = 1
    IMM = 2

class RiscCore(wiring.Component): # RISCV 32I implementation (32E has 16 regs)
    """
    RISCV implementation
    32I - without mul
    32M - with mul
    
    Internal connections to modules
    """
    def __init__(self, n_regs= 32, has_mul=True, normally_on=True):
        self.n_regs = 32
        self.has_mul = has_mul # Multiplication unit
        self.normally_on = normally_on
        
        super().__init__({
            "bus": Out(Bus(32, 32)),
            "size": Out(2),
            "prog": Out(Bus(32, 32)),
            "int": In(Bus(32, 8)),
            "debug": In(Bus(32, 32)) # Debugger access
        })
        
    def elaborate(self, platform):
        m = Module()
        
        pc = Signal(32)
        prog_enable = Signal(init=self.normally_on)
        
        # Signal prevents program read when pc might change
        latch = Signal()
        
        m.submodules.decode = decode = InstructionDecode()
        
        m.submodules.decode_buffer = decode_buffer = Buffer(decode_shape)
        
        wiring.connect(m, decode_buffer.consume, decode.produce)
        
        # Get instruction
        m.d.comb += self.prog.addr.eq(pc)
        m.d.comb += self.prog.cyc.eq(decode.consume.ready & prog_enable & (~latch))
        m.d.comb += self.prog.stb.eq(decode.consume.ready & prog_enable & (~latch))
        
        # latch if program counter might change
        with m.If(self.prog.cyc & self.prog.stb & self.prog.ack):
            with m.Switch(decode.consume.data.op):
                with m.Case(Instruction.BRANCH):
                    m.d.sync += latch.eq(1)
                with m.Case(Instruction.JAL):
                    m.d.sync += latch.eq(1)
                with m.Case(Instruction.JALR):
                    m.d.sync += latch.eq(1)
                with m.Default():
                    # Just go to the next program counter immediately
                    #m.d.sync += latch.eq(1)
                    m.d.sync += pc.eq(pc+4)
        
        # Data includes program counter and instruction data
        # This may give slightly different jump behavior,
        # Since this will make branching relative to the next instruction
        m.d.comb += decode.consume.data.pc.eq(pc)
        
        m.d.comb += decode.consume.data.as_value()[32:].eq(self.prog.r_data)
        
        m.d.comb += decode.consume.valid.eq(self.prog.ack)
        
        # ALU
        m.submodules.alu = alu = Alu()
        
        # Route decoder
        with m.Switch(decode_buffer.produce.data.op):
            with m.Case(Instruction.ARITHIMM):
                data = decode_buffer.produce.data.mode.imm
                # TODO move some of these outside of switch
                m.d.comb += [
                    alu.consume.s1.eq(data.s),
                    alu.consume.s2.eq(data.i),
                    alu.consume.function.eq(data.f),
                    alu.consume.mode.eq(data.m),
                    alu.consume.d.eq(data.d),
                    # Handshake
                    alu.consume.valid.eq(decode_buffer.produce.valid),
                    decode_buffer.produce.ready.eq(1)
                ]
            with m.Case(Instruction.ARITH):
                # Register arithmetic
                data = decode_buffer.produce.data.mode.arith
                m.d.comb += [
                    alu.consume.s1.eq(data.s1),
                    alu.consume.s2.eq(data.s2),
                    alu.consume.function.eq(data.f),
                    alu.consume.mode.eq(data.m),
                    alu.consume.d.eq(data.d),
                    alu.consume.valid.eq(decode_buffer.produce.valid),
                    decode_buffer.produce.ready.eq(1)
                ]
            with m.Case(Instruction.MEMORYSTORE):
                # Store word
                data = decode_buffer.produce.data.mode.store
                m.d.comb += [
                    self.bus.addr.eq(data.offset + data.s1),
                    self.bus.w_data.eq(data.s2),
                    self.bus.w_en.eq(1),
                    self.bus.stb.eq(decode_buffer.produce.valid),
                    self.bus.cyc.eq(decode_buffer.produce.valid),
                    decode_buffer.produce.ready.eq(self.bus.ack)
                ]
                m.d.comb += self.size.eq(data.offset)
            with m.Default():
                pass
        
        # Route result
        write_buffer = m.submodules.write_buffer = Buffer(write_shape)
        
        write_route = Signal(WriteRoute)
        
        # Write to register
        m.d.comb += [
            decode.write.addr.eq(write_buffer.produce.data.d),
            decode.write.w_data.eq(write_buffer.produce.data.value),
            decode.write.w_en.eq(1),
            decode.write.stb.eq(write_buffer.produce.valid),
            decode.write.cyc.eq(write_buffer.produce.valid),
            write_buffer.produce.ready.eq(decode.write.ack)
        ]
        
        with m.If(write_buffer.produce.valid & write_buffer.produce.ready):
            with m.If(latch):
                # TODO check for branch
                m.d.sync += latch.eq(0)
                m.d.sync += pc.eq(decode_buffer.produce.data.pc+4)
        
        with m.Switch(write_route):
            with m.Case(WriteRoute.ALU):
                # Write register from ALU
                m.d.comb += write_buffer.consume.data.value.eq(alu.produce.value)
                m.d.comb += write_buffer.consume.data.d.eq(alu.produce.d)
                m.d.comb += write_buffer.consume.valid.eq(alu.produce.valid)
            with m.Case(WriteRoute.IMM):
                # Write register from an immediate (i.e. AUIPC or LUI)
                m.d.comb += write_buffer.consume.data.value.eq(decode_buffer.produce.data.mode.upper.i)
                m.d.comb += write_buffer.consume.data.d.eq(decode_buffer.produce.data.mode.upper.d)
                m.d.comb += write_buffer.consume.valid.eq(decode_buffer.produce.valid)
                m.d.comb += decode_buffer.produce.ready.eq(write_buffer.consume.ready)
            with m.Default():
                pass
        
        # How are registers being written to
        with m.Switch(decode_buffer.produce.data.op):
            with m.Case(Instruction.ARITHIMM):
                m.d.comb += write_route.eq(WriteRoute.ALU)
            with m.Case(Instruction.ARITH):
                m.d.comb += write_route.eq(WriteRoute.ALU)
            with m.Case(Instruction.AUIPC):
                m.d.comb += write_route.eq(WriteRoute.IMM)
            with m.Case(Instruction.LUI):
                m.d.comb += write_route.eq(WriteRoute.IMM)
            with m.Default():
                m.d.comb += write_route.eq(WriteRoute.NONE)
        
        return m