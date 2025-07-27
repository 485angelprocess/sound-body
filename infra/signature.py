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
    async def sim_write(ctx, port, addr, data, sync = True):
        ctx.set(port.cyc, 1)
        ctx.set(port.stb, 1)
        ctx.set(port.w_en, 1)
        ctx.set(port.addr, addr)
        ctx.set(port.w_data, data)
        
        if sync:
            await ctx.tick().until(port.ack)
        else:
            while not ctx.get(port.ack):
                await ctx.delay(1e-6)
        
        ctx.set(port.cyc, 0)
        ctx.set(port.stb, 0)
        ctx.set(port.w_en, 0)
        
    @staticmethod
    async def write_consume(ctx, port, sync=True):
        while True:
            if ctx.get(port.cyc) and ctx.get(port.stb):
                ctx.set(port.ack, 1)
                addr, data = ctx.get(port.addr), ctx.get(port.w_data)
                print("Consumed {}: {}".format(addr, data))
                if not sync:
                    await ctx.delay(1e-6)
                ctx.set(port.ack, 0)
                return addr, data
            if sync:
                await ctx.tick()
            else:
                await ctx.delay(1e-6)
        
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
    def __init__(self, data_shape = 8, prefix = "", **kwargs):
        super().__init__({
            "{}data".format(prefix): Out(data_shape),
            "{}valid".format(prefix): Out(1),
            "{}ready".format(prefix): In(1)
        } | kwargs)
        
    @staticmethod
    async def write(ctx, port, data):
        ctx.set(port.valid, 1)
        ctx.set(port.data, data)
        await ctx.tick().until(port.ready)
        ctx.set(port.valid, 0)

    @staticmethod
    async def get(ctx, port):
        ctx.set(port.ready, 1)
        data, = await ctx.tick().sample(port.data).until(port.valid)
        ctx.set(port.ready, 0)
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
        
class Axi(wiring.Signature):
    def __init__(self, address_shape = 32, data_shape = 32):
        super().__init__({
            "awvalid": Out(1),
            "awready": In(1),
            "awaddr": Out(address_shape),
            "awlen": Out(8),
            "awsize": Out(2),
            "awburst": Out(2),
            "wdata": Out(data_shape),
            "wvalid": Out(1),
            "wready": In(1),
            "wlast": Out(1),
            "bresp": In(2),
            "bvalid": In(1),
            "bready": Out(1),
            "arvalid": Out(1),
            "arready": In(1),
            "araddr": Out(address_shape),
            "arlen": Out(8),
            "arsize": Out(2),
            "rdata": In(data_shape),
            "rvalid": In(1),
            "rready": Out(1),
            "rlast": In(1)
        })