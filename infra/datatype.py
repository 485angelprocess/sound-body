from amaranth.lib import data

class Float(data.Struct):
    fraction: 23
    exponent:  8 = 0x7f
    sign:      1

    def is_subnormal(self):
        return self.exponent == 0
        
    @staticmethod
    def mul_exponent(a, b):
        return a.exponent + b.exponent - 0x7F
        
    @staticmethod
    def mul_sign(a, b):
        return a.sign != b.sign