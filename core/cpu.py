"""
Implementation of RV32I instructions
"""
from amaranth import *
from amaranth.lib import wiring, enum, data
from amaranth.lib.wiring import In, Out
from infra.signature import Bus

from core.mul import MulSignature, MulUnit

class Instruction(enum.Enum):
    # These are the op codes for the base instruction set
    LUI         = 0b0110111 # Load upper immediate
    AUIPC       = 0b0010111 # Add upper immediate to program counter
    ARITHIMM    = 0b0010011
    JAL         = 0b1101111
    BRANCH      = 0b1100011
    JALR        = 0b1100111
    MEMORYLOAD  = 0b0000011
    MEMORYSTORE = 0b0100011
    ARITH       = 0b0110011
    FENCE       = 0b0001111
    E           = 0b1110011
    
class MemoryStage(enum.Enum):
    SETUP = 0
    RUN = 1
    
risc_instruction_layout = data.UnionLayout({
    "op": 7,
    "r": data.StructLayout({
        "op": 7,
        "rd": 5,
        "f_lower": 3,
        "rs1": 5,
        "rs2": 5,
        "f_upper":  7
    }),
    "i": data.StructLayout({
        "op": 7,
        "rd": 5,
        "f" : 3,
        "rs": 5,
        "imm":signed(12) 
    }),
    "u": data.StructLayout({
        "op":  7,
        "rd":  5,
        "imm": signed(20)
    }),
    "s": data.StructLayout({
        "op": 7,
        "imm_lower": 5,
        "f": 3,
        "rs1": 5,
        "rs2": 5,
        "imm_upper": 7
    }),
    "j": data.StructLayout({
        "op": 7,
        "rd": 5,
        "offset": signed(20)
    }),
    "b": data.StructLayout({
        "op": 7,
        "offset_lower": 5,
        "f": 3,
        "rs1": 5,
        "rs2": 5,
        "offset_upper": 7
    }),
    "m": data.StructLayout({
        "op": 7,
        "rd": 5,
        "f": 3,
        "rs1": 5,
        "rs2": 5,
        "muldiv": 7
    })
})
    
class CoreDebug(object):
    def __init__(self):
        self.instruction = None
        self.reg = None
        self.pc = None
    
class RiscCore(wiring.Component): # RISCV 32I implementation (32E has 16 regs)
    """
    RISCV implementation
    32I - without mul
    32M - with mul
    """
    def __init__(self, n_regs=32, has_mul=True):
        self.n_regs = 32
        self.has_mul = has_mul # Multiplication unit
        
        super().__init__({
            "bus": Out(Bus(32, 32)),
            "prog": Out(Bus(32, 32)),
            "mpu": In(MulSignature()),
            "fpu": Out(Bus(8, 32)), # For FPU unit
            "int": In(Bus(32, 8)),
            "debug": In(Bus(32, 32)) # Debugger access
        })
        
    def describe_branch(self, m, reg, instruction_cache):
        with m.Switch(instruction_cache.b.f):
            with m.Case(0b000):
                # Branch if Equal
                return reg[instruction_cache.b.rs1] == reg[instruction_cache.b.rs2]
            with m.Case(0b001):
                # Branch if not equal
                return reg[instruction_cache.b.rs1] != reg[instruction_cache.b.rs2]
            with m.Case(0b100):
                # Branch less than
                return reg[instruction_cache.b.rs1] < reg[instruction_cache.b.rs2]
            with m.Case(0b101):
                # Branch greater than or equal
                return reg[instruction_cache.b.rs1] >= reg[instruction_cache.b.rs2]
            with m.Case(0b110):
                # Branch less than unsigned
                return (
                    reg[instruction_cache.b.rs1].as_unsigned() <
                    reg[instruction_cache.b.rs2].as_unsigned()
                )
            with m.Case(0b111):
                # Branch less than signed
                return (
                    reg[instruction_cache.b.rs1].as_unsigned() >=
                    reg[instruction_cache.b.rs2].as_unsigned()
                )
                
    def describe_mul(self, m, reg, inst, fetch, active, stage):
        # Some of these should be moved out of conditionals probably?
        with m.If(stage == 0):
            m.d.sync += [
                self.mpu.muldiv.eq(inst.m.muldiv),
                self.mpu.f.eq(inst.m.f),
                self.mpu.a.eq(reg[inst.m.rs1]),
                self.mpu.b.eq(reg[inst.m.rs2]),
                self.mpu.en.eq(1),
                stage.eq(1)
            ]
        with m.Else():
            m.d.sync += self.mpu.en.eq(0)
            with m.If(self.mpu.done):
                m.d.sync += stage.eq(0)
                # finish operation
                m.d.sync += fetch.eq(1)
                m.d.sync += active.eq(0)
                # Get result
                m.d.sync += reg[inst.m.rd].eq(self.mpu.result)
            
    def describe_arith(self, m, reg, instruction_cache, fetch, active):
        m.d.sync += active.eq(0)
        with m.Switch(instruction_cache.r.f_lower):
            with m.Case(0b000):
                with m.If(instruction_cache.r.f_upper == 0b0000000):
                    # Add
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] +
                        reg[instruction_cache.r.rs2]
                    )
                with m.Elif(instruction_cache.r.f_upper == 0b0100000):
                    # Subtract
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] -
                        reg[instruction_cache.r.rs2]
                    )
                with m.Else():
                    pass
                    #m.d.sync += Assert(0, "Function not implemented")
            with m.Case(0b001):
                with m.If(instruction_cache.r.f_upper == 0b0000000):
                    # Shift left
                    # TODO not quite right,
                    # if rs2 is above a value, it's 0,
                    # otherwise actually shift
                    with m.If(reg[instruction_cache.r.rs2] > 5):
                        m.d.sync += reg[instruction_cache.r.rd].eq(0)
                    with m.Else():
                        m.d.sync += reg[instruction_cache.r.rd].eq(
                            reg[instruction_cache.r.rs1] <<
                            reg[instruction_cache.r.rs2].as_unsigned()[0:3]
                        )
                with m.Else():
                    pass
                    #m.d.sync += Assert(0, "Function not implemented")
            with m.Case(0b010):
                with m.If(instruction_cache.r.f_upper == 0b0000000):
                    # Less than
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] <
                        reg[instruction_cache.r.rs2]
                    )
            with m.Case(0b011):
                with m.If(instruction_cache.r.f_upper == 0b0000000):
                    # Unsigned less than
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1].as_unsigned() <
                        reg[instruction_cache.r.rs2].as_unsigned()
                    )
            with m.Case(0b100):
                with m.If(instruction_cache.r.f_upper == 0b000000):
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] ^
                        reg[instruction_cache.r.rs2]
                    )
            with m.Case(0b101):
                with m.If(instruction_cache.r.f_upper == 0b00000_00):
                    # Logical shift right
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] >>
                        reg[instruction_cache.r.rs2].as_unsigned()
                    )
                with m.Elif(instruction_cache.r.f_upper == 0b01000_00):
                    # Arithmetic shift right
                    m.d.sync += reg[instruction_cache.r.rd][0:31].eq(
                        reg[instruction_cache.r.rs1] >>
                                reg[instruction_cache.r.rs2].as_unsigned()
                            )
                    m.d.sync += reg[instruction_cache.r.rd][-1].eq(
                        reg[instruction_cache.r.rs1][-1]
                    )
            with m.Case(0b110):
                # OR
                with m.If(instruction_cache.r.f_upper == 0b00000_00):
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] |
                        reg[instruction_cache.r.rs2]
                    )
            with m.Case(0b111):
                # AND
                with m.If(instruction_cache.r.f_upper == 0b00000_00):
                    m.d.sync += reg[instruction_cache.r.rd].eq(
                        reg[instruction_cache.r.rs1] &
                        reg[instruction_cache.r.rs2]
                    )
        
    def elaborate(self, platform):
        m = Module()
        
        enable = Signal(init = 1)
        
        reg = Array([Signal(signed(32), name = "r{:02X}".format(i)) for i in range(32)])
        
        program_address_shape = 32
        
        program_counter = Signal(program_address_shape)
        
        m.d.comb += self.prog.addr.eq(program_counter)
        
        instruction_cache = Signal(risc_instruction_layout)
        instruction_fetch = Signal(risc_instruction_layout)
        
        # Debugger
        with m.If(self.debug.cyc & self.debug.stb):
            with m.If(self.debug.w_en):
                # TODO: consider direct read/write
                # TODO: add step or similiar type modes
                m.d.comb += self.debug.ack.eq(1)
            with m.Else():
                # Read
                m.d.comb += self.debug.ack.eq(1)
                with m.If(self.debug.addr == 0):
                    m.d.comb += self.debug.r_data.eq(ord('C'))
                with m.Elif(self.debug.addr < 32):
                    m.d.comb += self.debug.r_data.eq(reg[self.debug.addr])
                with m.If(self.debug.addr == 33):
                    m.d.comb += self.debug.r_data.eq(program_counter)
                with m.If(self.debug.addr == 34):
                    m.d.comb += self.debug.r_data.eq(instruction_fetch)
                with m.If(self.debug.addr == 35):
                    m.d.comb += self.debug.r_data.eq(instruction_cache)
        
        mem_counter = Signal(range(4))
        mem_register = Signal(32)
        mem_address = Signal(32)
        
        jal_offset = Signal(signed(21))
        
        # jal offset mapping
        # offset[20|10:1|11|19:12]
        m.d.comb += jal_offset[12:20].eq(instruction_cache.j.offset[0:8])
        m.d.comb += jal_offset[   11].eq(instruction_cache.j.offset[8])
        m.d.comb += jal_offset[ 1:11].eq(instruction_cache.j.offset[9:19])
        m.d.comb += jal_offset[   20].eq(instruction_cache.j.offset[19])
        
        branch_offset = Signal(signed(13))
        
        # branch offset mapping
        # offset_upper[12|10:5], offset_lower[4:1|11]
        m.d.comb += branch_offset.eq(
            (instruction_cache.b.offset_lower[0] << 11) +
            (instruction_cache.b.offset_lower[1:5] << 1) +
            (instruction_cache.b.offset_upper[0:6] << 5) +
            (instruction_cache.b.offset_upper[6] << 12)
        )
        
        branch_next = Signal(32)
        
        m.d.comb += branch_next.eq(
            program_counter +
            branch_offset - 4
        )
        
        branch_en = Signal()
        
        # This is for debugging information
        opcode = Signal(Instruction)
        m.d.comb += opcode.eq(instruction_fetch.op)
        
        opcode_cache = Signal(Instruction)
        m.d.comb += opcode_cache.eq(instruction_cache.op)
        
        fetch = Signal(init = 1)
            
        mode = Signal(Instruction)
        active = Signal()
            
        # Read program when active
        m.d.comb += self.prog.cyc.eq(enable & fetch)
        m.d.comb += self.prog.stb.eq(enable & fetch)
        
        m.d.comb += instruction_fetch.eq(self.prog.r_data)
        
        memorystage = Signal(MemoryStage)
        
        mulstage = Signal()
        
        with m.If(branch_en):
            m.d.sync += program_counter.eq(branch_next)
            m.d.sync += fetch.eq(1)
        
        #################################
        ## Run instruction ##############
        #################################
        with m.If(active):
            with m.Switch(opcode_cache):
                ###################################
                ###### Conditional branch #########
                ###################################
                with m.Case(Instruction.BRANCH):
                    m.d.sync += fetch.eq(1)
                    m.d.sync += active.eq(0)
                    m.d.comb += branch_en.eq(self.describe_branch(m, reg, instruction_cache))
                ##################################
                ### Load from memory #############
                ##################################
                with m.Case(Instruction.MEMORYLOAD):
                    with m.Switch(memorystage):
                        with m.Case(MemoryStage.SETUP):
                            # Load value from memory
                            offset = instruction_cache.i.imm
                            m.d.sync += mem_address.eq(reg[instruction_cache.i.rs] + offset.as_signed())
                            m.d.sync += reg[instruction_cache.i.rd].eq(0)
                            with m.Switch(instruction_cache.i.f):
                                with m.Case(0b010):
                                    # Load word
                                    pass
                                with m.Default():
                                    pass
                                    #m.d.sync += Assert(0, "Unimplemented load command")
                            m.d.sync += memorystage.eq(MemoryStage.RUN)
                        with m.Case(MemoryStage.RUN):
                            # Run n bus transactions to load data
                            m.d.comb += self.bus.cyc.eq(1)
                            m.d.comb += self.bus.stb.eq(1)
                            m.d.comb += self.bus.addr.eq(mem_address)
                            with m.If(self.bus.ack):
                                # Read ready
                                # Shift in data
                                m.d.sync += reg[instruction_cache.i.rd].eq(self.bus.r_data)
                                # Fetch next instruction
                                m.d.sync += active.eq(0)
                                m.d.sync += fetch.eq(1)
                                m.d.sync += memorystage.eq(MemoryStage.SETUP)
                ##########################################
                ## Store memory ##########################
                ##########################################
                with m.Case(Instruction.MEMORYSTORE):
                    with m.Switch(memorystage):
                        with m.Case(MemoryStage.SETUP):
                            offset = instruction_cache.s.imm_lower + (instruction_cache.s.imm_upper << 5)
                            m.d.sync += mem_address.eq(reg[instruction_cache.s.rs1] + offset.as_signed())
                            with m.Switch(instruction_cache.s.f):
                                with m.Case(0b010):
                                    # Store word
                                    m.d.sync += mem_register.eq(reg[instruction_cache.s.rs2][0:32])
                                with m.Default():
                                    pass
                                    #m.d.sync += Assert(0, "Unimplemented store command")
                            m.d.sync += memorystage.eq(MemoryStage.RUN)
                        with m.Case(MemoryStage.RUN):
                            # Shift out bytes of data
                            # Alternatively could add a flag for width of data
                            m.d.comb += self.bus.cyc.eq(1)
                            m.d.comb += self.bus.stb.eq(1)
                            m.d.comb += self.bus.w_en.eq(1)
                            
                            m.d.comb += self.bus.addr.eq(mem_address)
                            m.d.comb += self.bus.w_data.eq(mem_register)
                            
                            with m.If(self.bus.ack):
                                m.d.sync += active.eq(0)
                                m.d.sync += fetch.eq(1)
                                # Finished writing bytes to memory
                                m.d.sync += memorystage.eq(MemoryStage.SETUP)
                ###################################
                ### Register integer operations ##
                ###################################
                with m.Case(Instruction.ARITH):
                    if self.has_mul:
                        with m.If(instruction_cache.r.f_upper == 0x1):
                            #multiplication
                            self.describe_mul(m, reg, instruction_cache, fetch, active, mulstage)
                        with m.Else():
                            # Normal operation
                            self.describe_arith(m, reg, instruction_cache, fetch, active)
                    else:
                        self.describe_arith(m, reg, instruction_cache, fetch, active)
                #################################
                ### immediate instructions ######
                #################################
                with m.Case(Instruction.ARITHIMM):
                    m.d.sync += active.eq(0)
                    with m.Switch(instruction_cache.i.f):
                        with m.Case(0b000): # ADDI
                            # Add immediate
                            m.d.sync += reg[instruction_cache.i.rd].eq(
                                reg[instruction_cache.i.rs] +
                                instruction_cache.i.imm
                            )
                        with m.Case(0b010): #SLTI
                            # Set less than immeddiate
                            m.d.sync += reg[instruction_cache.i.rd].eq(
                                reg[instruction_cache.i.rs] <
                                instruction_cache.i.imm
                            )
                        with m.Case(0b011): # SLTIU
                            # Set less than immediate unsigned
                            m.d.sync += reg[instruction_cache.i.rd].eq(
                                reg[instruction_cache.i.rs].as_unsigned() <
                                instruction_cache.i.imm.as_unsigned()
                            )
                        with m.Case(0b100): # XORI
                            # bitwise xori
                            m.d.sync += reg[instruction_cache.i.rd].eq(
                                reg[instruction_cache.i.rs] ^
                                instruction_cache.i.imm
                            )
                        with m.Case(0b111): # ANDI
                            # And immediate
                            m.d.sync += reg[instruction_cache.i.rd].eq(
                                reg[instruction_cache.i.rs] &
                                instruction_cache.i.imm
                            )
                        with m.Case(0b001): # SLLI
                            # Shift left
                            m.d.sync += reg[instruction_cache.i.rd].eq(
                                reg[instruction_cache.i.rs] <<
                                instruction_cache.i.imm[0:5].as_unsigned()
                            )
                        with m.Case(0b101): # SRLI
                            with m.If(instruction_cache.as_value()[27:] == 0b00000):
                                # Shift right logical
                                m.d.sync += reg[instruction_cache.i.rd].eq(
                                    reg[instruction_cache.i.rs] >>
                                    instruction_cache.i.imm[0:5].as_unsigned()
                                )
                            with m.Elif(instruction_cache.as_value()[27:] == 0b01000):
                                # Shift right arithmetic
                                m.d.sync += reg[instruction_cache.i.rd][0:31].eq(
                                    reg[instruction_cache.i.rs] >>
                                    instruction_cache.i.imm[0:5].as_unsigned()
                                )
                                m.d.sync += reg[instruction_cache.i.rd][-1].eq(
                                    reg[instruction_cache.i.rs][-1]
                                )
                            with m.Else():
                                pass
                                #m.d.sync += Assert(0, "Shift function not implemented")
                        with m.Default():
                            pass
                            #m.d.sync += Assert(0, "Function not implemented")
                with m.Case(Instruction.LUI):
                    # Load upper immediate
                    m.d.sync += active.eq(0)
                    m.d.sync += reg[instruction_cache.u.rd].eq(
                        instruction_cache.u.imm << 12
                    )
                with m.Case(Instruction.AUIPC):
                    # Add upper immediate to pc
                    m.d.sync += active.eq(0)
                    
                    # TODO check if this is relative to 
                    # the next program counter or the previous
                    m.d.sync += reg[instruction_cache.u.rd].eq(
                        program_counter - 4 +
                        (instruction_cache.u.imm << 12)
                    )
                with m.Case(Instruction.JAL):
                    # jump and link
                    m.d.sync += active.eq(0)
                    m.d.sync += reg[instruction_cache.j.rd].eq(
                        program_counter
                    )
                    m.d.sync += program_counter.eq(
                        program_counter + jal_offset
                    )
                with m.Case(Instruction.JALR):
                    # jump and link register
                    m.d.sync += active.eq(0)
                    m.d.sync += reg[instruction_cache.i.rd].eq(
                        program_counter
                    )
                    m.d.sync += program_counter.eq(
                        (reg[instruction_cache.i.rs] +
                        instruction_cache.i.imm.as_signed())
                        & ~1
                    )
                with m.Default():
                    pass
                    #m.d.sync += Assert(0, "Unimplemented Instruction")
        
        ####################
        ## Fetch ###########
        ####################
        # Instruction is ready
        with m.If(self.prog.cyc & self.prog.stb & self.prog.ack):
            m.d.sync += instruction_cache.eq(self.prog.r_data)
            m.d.sync += program_counter.eq(program_counter + 4)
            m.d.sync += active.eq(1)
            
            m.d.sync += fetch.eq(0)
            
            m.d.sync += self.mpu.en.eq(0)
            
            # Fetch can occur while operation is running
            # These all always take one cycle
            for single in (Instruction.ARITHIMM, Instruction.AUIPC, Instruction.LUI, Instruction.JAL, Instruction.JALR):
                with m.If(opcode == single):
                    m.d.sync += fetch.eq(1)
                    
            # Non multiplication
            with m.If((opcode == Instruction.ARITH) & 
                    (instruction_fetch.r.f_upper != 0x01)):
                m.d.sync += fetch.eq(1)
                   
        self.debug = CoreDebug()
        
        self.debug.pc = program_counter
        self.debug.reg = reg
        self.instruction = instruction_fetch
        
        return m
    
