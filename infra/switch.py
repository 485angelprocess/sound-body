from amaranth import *
from amaranth.lib import wiring, memory, enum
from amaranth.lib.wiring import In, Out

from infra.signature import Bus

class RangeToDest(wiring.Component):
    def __init__(self, data_shape = 8, major = (16,32), minor = (0,16), dest_shape = 1):
        self.major = major
        self.minor = minor
        
        super().__init__({
            "consume": In(Bus(32, data_shape)),
            "produce": Out(Bus(32, data_shape, dest_shape = dest_shape))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        m.d.comb += [
            # Split address and destination at points
            self.produce.addr.eq(self.consume.addr[self.minor[0]:self.minor[1]]),
            self.produce.dest.eq(self.consume.addr[self.major[0]:self.major[1]]),
            
            # Transaction
            self.produce.stb.eq(self.consume.stb),
            self.produce.cyc.eq(self.consume.cyc),
            self.consume.ack.eq(self.produce.ack),
            
            self.produce.w_en.eq(self.consume.w_en),
            
            # Data
            self.produce.w_data.eq(self.consume.w_data),
            self.consume.r_data.eq(self.produce.r_data)
        ]
        
        return m

class DestToAddress(wiring.Component):
    def __init__(self, shift = 16, dest_shape = 1):
        self.shift = shift
        
        super().__init__({
            "consume": In(Bus(32, 32, dest_shape = dest_shape)),
            "produce": Out(Bus(32, 32))
        })
        
    def elaborate(self, platform):
        m = Module()
        
        m.d.comb += [
            # Split address and destination at points
            self.produce.addr.eq(self.consume.addr + (self.consume.dest << self.shift)),
            self.produce.dest.eq(0),
            
            # Transaction
            self.produce.stb.eq(self.consume.stb),
            self.produce.cyc.eq(self.consume.cyc),
            self.consume.ack.eq(self.produce.ack),
            
            self.produce.w_en.eq(self.consume.w_en),
            
            # Data
            self.produce.w_data.eq(self.consume.w_data),
            self.consume.r_data.eq(self.produce.r_data)
        ]
        
        return m
        
class BusDebug(object):
    def __init__(self, size=2):
        self.cyc = [None for _ in range(size)]
        self.w_en = [None for _ in range(size)]
        self.select = None

class SwitchPortDef(object):
    def __init__(self, addr=32, data=32):
        self.addr = addr
        self.data = data

class BusSwitch(wiring.Component):
    """
    Switch based on dest
    """

    def __init__(self, ports, addr=32, data=32, num_inputs=2):
        self.n = len(ports)
        
        self.num_inputs = num_inputs
        
        p = dict()
        for i in range(len(ports)):
            p["p_{:02X}".format(i)] = Out(Bus(ports[i].addr, ports[i].data))
        
        c = dict()
        for i in range(num_inputs):
            c["c_{:02X}".format(i)] = In(Bus(addr, data))
        
        super().__init__(c | p)
        
    def elaborate(self, platform):
        m = Module()
        
        select = Signal(range(self.num_inputs))
        
        consume = [getattr(self, "c_{:02X}".format(i)) for i in range(self.num_inputs)]
        
        # For visualizing
        self.debug = BusDebug()
        
        self.debug.cyc = [c.cyc for c in consume]
        self.debug.ack = [c.ack for c in consume]
        
        self.debug.w_en = [c.w_en for c in consume]
        
        self.debug.select = select
        
        for i in range(len(consume)):
            c = consume[i]
            with m.If(select == i):
                with m.If(~c.cyc):
                    # Check other input
                    with m.If(select == len(consume) - 1):
                        m.d.sync += select.eq(0)
                    with m.Else():
                        m.d.sync += select.eq(select + 1)
                p = getattr(self, "p_{:02X}".format(0))
                m.d.comb += [
                    p.stb.eq(c.stb),
                    p.cyc.eq(c.cyc),
                    c.ack.eq(p.ack),
                    p.addr.eq(c.addr),
                    p.w_en.eq(c.w_en),
                    p.w_data.eq(c.w_data),
                    c.r_data.eq(p.r_data)
                ]
        
        return m
        
class AddressSwitch(wiring.Component):
    """
    Splits incoming bus based on address
    """
    def __init__(self, split=256):
        """
        :arg split: address to split at
        """
        self.split = [split]
        
        super().__init__({
            "consume": In(Bus(32, 32)),
            # Lower address
            "a": Out(Bus(32, 32)),
            # Upper address
            "b": Out(Bus(32, 32)),
            # TODO dynamically create ports
        })
        
    def get_port(self, i):
        if i == 0:
            return self.a
        else:
            return self.b
        
    def elaborate(self, platform):
        m = Module()
        
        # A not B
        select = Signal(range(len(self.split)+1))
        
        with m.If(self.consume.addr < self.split[0]):
            m.d.comb += select.eq(0)
        for i in range(1, len(self.split)-1):
            with m.Elif(self.consume.addr < self.split[i]):
                m.d.comb += select.eq(i)
        with m.Else():
            m.d.comb += select.eq(len(self.split))

        address = Array([
                        Signal(32, name="{}_address".format(i)) for i in range(len(self.split))
                    ])
        for i in range(len(self.split)):
            m.d.comb += address[i].eq(self.consume.addr - self.split[i])
        
        m.d.comb += [
            self.a.addr.eq(self.consume.addr),
            self.a.w_en.eq(self.consume.w_en),
            self.a.w_data.eq(self.consume.w_data)
        ]
        
        for i in range(len(self.split)):
            p = self.get_port(i+1)
            m.d.comb += [
                p.addr.eq(address[i]),
                p.w_en.eq(self.consume.w_en),
                p.w_data.eq(self.consume.w_data)
            ]
        
        # Direct to a or b
        with m.Switch(select):
            for i in range(len(self.split)+1):
                with m.Case(i):
                    p = self.get_port(i)
                    m.d.comb += [
                        p.stb.eq(self.consume.stb),
                        p.cyc.eq(self.consume.cyc),
                        self.consume.ack.eq(p.ack),
                        self.consume.r_data.eq(p.r_data)
                    ]
        
        return m