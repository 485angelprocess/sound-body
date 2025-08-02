from amaranth import signed
from amaranth.lib import enum, data

class Instruction(enum.Enum,shape=7):
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

instruction_shape = data.StructLayout({
    "pc": 32,
    "op": Instruction,
    "mode": data.UnionLayout({
        "r": data.StructLayout({
            "rd": 5,
            "f_lower": 3,
            "rs1": 5,
            "rs2": 5,
            "f_upper":  7
        }),
        "i": data.StructLayout({
            "rd": 5,
            "f" : 3,
            "rs": 5,
            "imm":signed(12) 
        }),
        "u": data.StructLayout({
            "rd":  5,
            "imm": signed(20)
        }),
        "s": data.StructLayout({
            "imm_lower": 5,
            "f": 3,
            "rs1": 5,
            "rs2": 5,
            "imm_upper": 7
        }),
        "j": data.StructLayout({
            "rd": 5,
            "offset": 20
        }),
        "b": data.StructLayout({
            "offset_lower": 5,
            "f": 3,
            "rs1": 5,
            "rs2": 5,
            "offset_upper": 7
        }),
        "m": data.StructLayout({
            "rd": 5,
            "f": 3,
            "rs1": 5,
            "rs2": 5,
            "muldiv": 7
        })
    })
})

decode_shape = data.StructLayout({
    "pc": 32,
    "op": Instruction,
    "mode": data.UnionLayout({
        "arith": data.StructLayout({
            # ALU
            "f": 3,
            "m": 7,
            "s1": signed(32),
            "s2": signed(32),
            "d": 5
        }),
        "imm": data.StructLayout({
            "f": 3,
            "m": 7,
            "s": signed(32),
            "i": signed(12),
            "d": 5
        }),
        "store": data.StructLayout({
            "f": 3,
            "offset": signed(12),
            "s1": signed(32),
            "s2": signed(32)
        }),
        "upper": data.StructLayout({
            "d": 5,
            "i": signed(32)
        }),
        "jump": data.StructLayout({
            "d": 5,
            "t": signed(32)
        }),
        "branch": data.StructLayout({
            "f": 3,
            "offset": signed(13),
            "s1": signed(32),
            "s2": signed(32)
        })
    })
})

write_shape = data.StructLayout({
    "d": 5,
    "value": 32
})