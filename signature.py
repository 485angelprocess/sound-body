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
        
    @staticmethod
    async def sim_write(ctx, port, addr, data):
        ctx.set(port.cyc, 1)
        ctx.set(port.stb, 1)
        ctx.set(port.w_en, 1)
        ctx.set(port.addr, addr)
        ctx.set(port.w_data, data)
        
        await ctx.tick().until(port.ack)
        
        ctx.set(port.cyc, 0)
        ctx.set(port.stb, 0)
        ctx.set(port.w_en, 0)
        
    @staticmethod
    async def sim_read(ctx, port, addr):
        ctx.set(port.cyc, 1)
        ctx.set(port.stb, 1)
        ctx.set(port.w_en, 0)
        
        ctx.set(port.addr, addr)
        
        response, = await ctx.tick().sample(port.r_data).until(port.ack)
        
        ctx.set(port.cyc, 0)
        ctx.set(port.stb, 0)
        
        return response
        
class MockBusDevice(object):
    def __init__(self):
        self.register = dict()
    
    async def run(self, ctx, port):
        if ctx.get(port.cyc) and ctx.get(port.stb):
            ctx.set(port.ack, 1)
            
            addr = ctx.get(port.addr)
            
            if ctx.get(port.w_en):
                self.register[addr] = ctx.get(port.w_data)
            else:
                ctx.set(port.r_data, self.register[addr])
        await ctx.tick()
    
    
class Stream(wiring.Signature):
    def __init__(self, data_shape = 8, **kwargs):
        super().__init__({
            "tdata": Out(data_shape),
            "tvalid": Out(1),
            "tready": In(1)
        } | kwargs)
        
    @staticmethod
    async def sim_write(ctx, port, data):
        ctx.set(port.tvalid, 1)
        ctx.set(port.tdata, data)
        await ctx.tick().until(port.tready)
        ctx.set(port.tvalid, 0)
        
        
    @staticmethod
    async def sim_get(ctx, port):
        ctx.set(port.tready, 1)
        data, = await ctx.tick().sample(port.tdata).until(port.tvalid)
        #print("Got data {}", data)
        ctx.set(port.tready, 0)
        return data
        
class AxiLite(wiring.Signature):
    def __init__(self, address_shape = 32, data_shape = 32):
        super().__init__({
            "awvalid": Out(1),
            "awready": In(1),
            "awaddr": Out(address_shape),
            "wdata": Out(data_shape),
            "wvalid": Out(1),
            "wready": In(1),
            "arvalid": Out(1),
            "arready": In(1),
            "araddr": Out(address_shape),
            "rdata": In(data_shape),
            "rvalid": In(1),
            "rready": Out(1),
            "bresp": In(2),
            "bready": Out(1),
            "bvalid": In(1)
        })