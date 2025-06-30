from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

class Bus(wiring.Signature):
    def __init__(self, addr_shape, data_shape):
        super().__init__({
            "cyc": Out(1),
            "stb": Out(1),
            "addr": Out(addr_shape),
            "ack": In(1),
            "w_en": Out(1),
            "w_data": Out(data_shape),
            "r_data": In(data_shape)
        })