"""
Decode instruction
"""
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from core.shape import instruction_shape, decode_shape, Instruction
from infra.signature import Stream, Bus

class RegisterMask(wiring.Component):
    """
    Logic for checking if registers can be read from
    """
    def __init__(self):
        super().__init__({
            "r_rd": In(5),
            "r_rs1": In(5),
            "r_rs2": In(5),
            "r_valid": In(1),
            "r_ok1": Out(1),
            "r_ok2": Out(1),
            "w_rd": In(5),
            "w_valid": In(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        reg_mask = Signal(32)
        
        r1_ok = Signal()
        r2_ok = Signal()
        
        # Can we read from a register, or do we have to wait
        m.d.comb += r1_ok.eq( ~((1 << self.r_rs1) & (reg_mask)) )
        m.d.comb += r2_ok.eq( ~((1 << self.r_rs2) & (reg_mask)) )
        
        m.d.comb += self.r_ok1.eq(r1_ok)
        m.d.comb += self.r_ok2.eq(r2_ok)
        
        # Add new destination register to mask
        with m.If(self.r_valid):
            m.d.sync += reg_mask.eq(reg_mask | (1 << self.r_rd))
        
        # Clear destination register from mask
        with m.If(self.w_valid):
            m.d.sync += reg_mask.eq(reg_mask & (~(1 << self.w_rd)))
        
        return m
        
class RegisterDevice(wiring.Component):
    """
    Read and write from registers
    """
    def __init__(self):
        super().__init__({
            "rs1": In(Bus(5, 32)),
            "rs2": In(Bus(5, 32)),
            "r_rd": In(5),
            "r_valid": In(1),
            "rd": In(Bus(5, 32)),
        })
        
    def elaborate(self, platform):
        m = Module()
        
        reg = Array([Signal(32, name="r{:02X}".format(i)) for i in range(32)])
        
        m.submodules.mask = mask = RegisterMask()
        
        # What destination register is going to be written to
        m.d.comb += mask.r_valid.eq(self.r_valid)
        m.d.comb += mask.r_rd.eq(self.r_rd)
        
        # Source registers
        m.d.comb += mask.r_rs1.eq(self.rs1.addr)
        m.d.comb += mask.r_rs2.eq(self.rs2.addr)
        
        m.d.comb += self.rs1.r_data.eq(reg[self.rs1.addr])
        m.d.comb += self.rs2.r_data.eq(reg[self.rs2.addr])
        
        # Give ack if register can be read from
        m.d.comb += self.rs1.ack.eq(mask.r_ok1)
        m.d.comb += self.rs2.ack.eq(mask.r_ok2)
        
        # Write to register
        m.d.comb += mask.w_valid.eq(self.rd.cyc & self.rd.stb)
        m.d.comb += mask.w_rd.eq(self.rd.addr)
        # Writes are always allowed
        m.d.comb += self.rd.ack.eq(self.rd.cyc & self.rd.stb)
        
        with m.If(self.rd.cyc & self.rd.stb):
            with m.If(self.rd.w_en):
                m.d.sync += reg[self.rd.addr].eq(self.rd.w_data)
            with m.Else():
                m.d.comb += self.rd.r_data.eq(reg[self.rd.addr])
        
        return m
    
class InstructionDecode(wiring.Component):
    """
    Decode instructions
    
    Consumes a stream of instructions,
    Produces stream with source register data
    
    Write bus writes to register
    Error bus provies errors
    """
    def __init__(self):
        super().__init__({
            "consume": In(Stream(instruction_shape)),
            "produce": Out(Stream(decode_shape)),
            "write": In(Bus(5, 32)), # Write to registers
            "debug": In(Bus(5, 32)), # TODO debug write directly to registers
            "error": Out(Bus(1, 32))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        # Keeps track of register read/writes
        m.submodules.reg = reg = RegisterDevice()
        
        register_ready = Signal()
        error_flag = Signal()
        
        # Number of registers being read from
        num_regs = Signal(2)
        # Is there going to be a register written to
        reg_write = Signal()
        
        m.d.comb += reg.r_rd.eq(self.consume.data.mode.r.rd)
        # Mask register being written
        m.d.comb += reg.r_valid.eq(reg_write & self.consume.ready & self.consume.valid)
        
        m.d.comb += self.consume.ready.eq(register_ready & self.produce.ready & (~error_flag))
        m.d.comb += self.produce.valid.eq(self.consume.valid & register_ready & (~error_flag))
        
        out_register = self.produce.data
        
        # Transfer op code and program counter
        m.d.comb += [
            out_register.op.eq(self.consume.data.op),
            out_register.pc.eq(self.consume.data.pc)
        ]
        
        # Mapping out data
        with m.Switch(self.consume.data.op):
            with m.Case(Instruction.ARITH):
                # Arithmetic
                m.d.comb += [
                    out_register.mode.arith.f.eq(self.consume.data.mode.r.f_lower),
                    out_register.mode.arith.s1.eq(reg.rs1.r_data),
                    out_register.mode.arith.s2.eq(reg.rs2.r_data),
                    out_register.mode.arith.m.eq(self.consume.data.mode.r.f_upper),
                    out_register.mode.arith.d.eq(self.consume.data.mode.r.rd)
                ]
            with m.Case(Instruction.ARITHIMM):
                # Arithmetic immediate
                m.d.comb += [
                    out_register.mode.imm.f.eq(self.consume.data.mode.i.f),
                    out_register.mode.imm.s.eq(reg.rs1.r_data),
                    # May be shifted i forget
                    out_register.mode.imm.i.eq(self.consume.data.mode.i.imm),
                    out_register.mode.imm.d.eq(self.consume.data.mode.i.rd)
                ]
            with m.Case(Instruction.MEMORYLOAD):
                # load memory
                m.d.comb += [
                    out_register.mode.imm.f.eq(self.consume.data.mode.i.f),
                    out_register.mode.imm.s.eq(reg.rs1.r_data),
                    out_register.mode.imm.i.eq(self.consume.data.mode.i.imm),
                    out_register.mode.imm.d.eq(self.consume.data.mode.i.rd)
                ]
            with m.Case(Instruction.MEMORYSTORE):
                # Store word
                m.d.comb += [
                    out_register.mode.store.f.eq(self.consume.data.mode.s.f),
                    out_register.mode.store.offset.eq(Cat(
                            self.consume.data.mode.s.imm_lower,
                            self.consume.data.mode.s.imm_upper)),
                    out_register.mode.store.s1.eq(reg.rs1.r_data),
                    out_register.mode.store.s2.eq(reg.rs2.r_data)
                ]
            with m.Default():
                m.d.comb += error_flag.eq(1)
                m.d.comb += self.error.cyc.eq(1)
                m.d.comb += self.error.stb.eq(1)
                m.d.comb += self.error.w_en.eq(1)
                m.d.comb += self.error.w_data.eq(self.consume.data.op)
        
        # Which registers are being read from
        m.d.comb += reg.rs1.addr.eq(self.consume.data.mode.r.rs1)
        m.d.comb += reg.rs2.addr.eq(self.consume.data.mode.r.rs2)
        
        # Read from register device
        with m.Switch(num_regs):
            with m.Case(1):
                m.d.comb += reg.rs1.cyc.eq(self.consume.valid)
                m.d.comb += reg.rs1.stb.eq(self.consume.valid)
                m.d.comb += register_ready.eq(reg.rs1.ack)
            with m.Case(2):
                m.d.comb += reg.rs1.cyc.eq(self.consume.valid)
                m.d.comb += reg.rs1.stb.eq(self.consume.valid)
                m.d.comb += reg.rs2.cyc.eq(self.consume.valid)
                m.d.comb += reg.rs2.stb.eq(self.consume.valid)
                m.d.comb += register_ready.eq(reg.rs1.ack & reg.rs1.ack)
            with m.Default():
                m.d.comb += register_ready.eq(1)
    
        # Is this stage ready
        with m.Switch(self.consume.data.op):
            with m.Case(Instruction.ARITH):
                # Reads from rs1 and rs2
                m.d.comb += num_regs.eq(2)
                m.d.comb += reg_write.eq(1)
            with m.Case(Instruction.ARITHIMM):
                # Read from rs1
                m.d.comb += num_regs.eq(1)
                m.d.comb += reg_write.eq(1)
            with m.Case(Instruction.MEMORYLOAD):
                m.d.comb += num_regs.eq(1)
                m.d.comb += reg_write.eq(1)
            with m.Case(Instruction.MEMORYSTORE):
                m.d.comb += num_regs.eq(2)
                m.d.comb += reg_write.eq(0)
            with m.Default():
                pass
                
        with m.If(~self.error.cyc):
            # normal operation
            m.d.comb += [
                reg.rd.addr.eq(self.write.addr),
                reg.rd.cyc.eq(self.write.cyc),
                reg.rd.stb.eq(self.write.stb),
                reg.rd.w_data.eq(self.write.w_data),
                reg.rd.w_en.eq(self.write.w_en),
                self.debug.r_data.eq(reg.rd.r_data),
                self.write.ack.eq(reg.rd.ack)
            ]
        with m.Else():
            # Debugger
            m.d.comb += [
                reg.rd.addr.eq(self.debug.addr),
                reg.rd.cyc.eq(self.debug.cyc),
                reg.rd.stb.eq(self.debug.stb),
                reg.rd.w_data.eq(self.debug.w_data),
                reg.rd.w_en.eq(self.debug.w_en),
                self.debug.r_data.eq(reg.rd.r_data),
                self.debug.ack.eq(reg.rd.ack)
            ]
        
        return m