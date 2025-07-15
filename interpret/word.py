"""
Wa
"""
class R(object):
    """
    Register in line
    """
    PREFIX = "x"
    OFFSET_FORMAT = "{offset}({prefix}{reg})" # Versus {offset}({reg})
    
    def __init__(self, r, offset = None):
        self.r = r
        self.offset = offset
        
    def assign(self, *args):
        pass
        
    def __str__(self):
        if self.offset is None:
            return "{}{}".format(R.PREFIX, self.r)
        else:
            return R.OFFSET_FORMAT.format(offset = self.offset, prefix = R.PREFIX, reg = self.r)

    @classmethod
    def sp(cls, offset = None):
        """
        Stack pointer
        """
        return cls(1, offset = offset)
        
    @classmethod
    def push(cls, offset = None):
        return cls(2, offset = offset)
        
    @classmethod
    def pull(cls, offset = None):
        return cls(3, offset = offset)
        
    @classmethod
    def tag(cls, offset = None):
        """
        Data tag
        """
        return cls(6, offset = offset)
        
    @classmethod
    def value(cls, offset = None):
        """
        Value for stack
        """
        return cls(7, offset = offset)
        
    @classmethod
    def zero(cls, offset = None):
        """
        Constant 0 register
        """
        return cls(0, offset = offset)
        
    @classmethod
    def ret(cls, offset = None):
        """
        Return address register
        """
        return cls(9, offset = offset)
        
    @classmethod
    def work(cls, n = 0, offset = None):
        """
        Working registers
        """
        return cls(10 + n, offset = offset)

class C(object):
    """
    Constant in line
    """
    def __init__(self, c):
        self.c = c
        
    def assign(self, *args):
        pass
        
    def __str__(self):
        return "{}".format(self.c)
        
class ArgException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        
class Arg(object):
    """
    Argument position,
    only doing constants for now
    """
    def __init__(self, i, default = None):
        self.i = i
        self.default = default
        self.a = None
        
    def assign(self, args):
        if len(args) > self.i:
            self.a = int(args[self.i])
        else:
            self.a = self.default
        
    def __str__(self):
        if self.a is None:
            raise ArgException("Argument is not assigned to")
        return "{}".format(self.a)

class Line(object):
    def __init__(self, *program, label = None):
        self.program = program
        self.label = label
        
    def assign(self, args):
        # TODO pre-process smaller list of assignable things
        [p.assign(args) for p in self.program if hasattr(p, "assign")]
        
    def __str__(self):
        msg = ""
        if self.label is not None:
            if len(self.label) < 5:
                msg += "{}:\t\t".format(self.label)
            else:
                msg += "{}:\t".format(self.label)
        else:
            msg += "\t\t"
        if len(self.program) > 0:
            msg += "{}\t".format(str(self.program[0]))
        if len(self.program) > 1:
            msg += ", ".join([str(self.program[i]) for i in range(1, len(self.program))])
        return msg
    
    def call(self, ctx):
        return self
        
class Word(object):
    def __init__(self, w):
        self.w = w
        
    def call(self, ctx):
        return ctx.read(self.w)
        
class Translation(object):
    def __init__(self, *program, result = R(0), desc = None):
        self.program = list(program)
        self.desc = desc
        self.args = None
        self.result = result
        
    def clear(self):
        self.program = list()
        
    def copy(self):
        return Translation(
            *[p for p in self.program],
            result = self.result,
            desc = self.desc
        )
        
    def assign(self, *args):
        self.args = args
        [l.assign(args) for l in self.program]
        
    def __add__(self, other):
        """
        Combine programs, with result being passed along
        """
        raise Exception("Add not implemented")
        
    def push(self, l):
        self.program.append(l)
        
    def set_callback(self, fn):
        self.call = fn
        return self
        
    def call(self, ctx):
        if self.program is not [None]:
            self.program = [p.call(ctx) for p in self.program if hasattr(p, "call")]
        
    def __str__(self):
        msg = ""
        if self.desc is not None:
            if self.args is not None:
                msg += "\t# {}: {}\n".format(self.desc, self.args)
            else:
                msg += "\t# {}\n".format(self.desc)
        return msg + "\n".join([str(l) for l in self.program]) + "\n"