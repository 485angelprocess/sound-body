import unittest

from amaranth.sim import *

from serial.i2c import I2CTop
from serial.serial_to_wishbone import SerialToWishbone
from serial.uart import UartTx, UartRx
from signature import Bus, MockBusDevice, Stream

class I2CWord(object):
    def __init__(self, data, ack = 0, read = False):
        self.data = data
        self.ack = ack
        self.read = read
        
        self.counter = 0
        
    def next(self):
        if self.counter < 8:
            # Get data msb
            return ((self.data << self.counter) & 0b1000_000) > 1, self.read
        else:
            return self.ack, True

    def last(self):
        return self.counter > 8
        
class I2CResponse(object):
    def __init__(self, *words):
        self.words = list(words)
        self.counter = 0
        
        self.last_scl = 0
        self.last_sda = 0
        
        self.en = 0
        
    def next(self):
        b, en = self.words[self.counter].next()
        if self.words[self.counter].last():
            self.counter += 1
        return b, en
    
    def last(self):
        return self.counter == len(self.words)
        
    def init(self, ctx, sda):
        ctx.set(sda, 1)
        
    def get(self, ctx, sda, scl, sda_in):
        if self.last_scl == 1 and scl == 0:
            # Falling edge
            b, en = self.next()
            self.en = en
            if en:
                ctx.set(sda_in, b)
            else:
                ctx.set(sda_in, sda)
        else:
            if self.en == 0:
                ctx.set(sda_in, sda)
        
        if self.last_scl == 1 and scl == 1:
            if sda == 0 and self.last_sda == 1:
                # Stop
                print("Stop")
                ctx.set(sda_in, 1)
            if sda == 1 and self.last_sda == 0:
                # Start
                print("Start")
                
        self.last_scl = scl
        self.last_sda = sda

class TestSerial(unittest.TestCase):
    def test_write(self):
        dut = I2CTop()
        
        response = I2CResponse(
            I2CWord(10),
            I2CWord(11),
            I2CWord(12),
            I2CWord(13)
        )
        
        async def bus_process(ctx):
            await Bus.sim_write(ctx, dut.bus, 8, 10) # Period
            await Bus.sim_write(ctx, dut.bus, 3, 1) # Write
            await Bus.sim_write(ctx, dut.bus, 2, 1) # Start flag
            await Bus.sim_write(ctx, dut.bus, 1, 10) # Write data
            await Bus.sim_write(ctx, dut.bus, 1, 11)
            await Bus.sim_write(ctx, dut.bus, 1, 12)
            await Bus.sim_write(ctx, dut.bus, 1, 13)
            assert await Bus.sim_read(ctx, dut.bus, 4) == 4
            await Bus.sim_write(ctx, dut.bus, 0, 1) # Enable
            
            # Wait for buffer to fill
            while await Bus.sim_read(ctx, dut.bus, 6) < 4:
                await ctx.tick()
            await Bus.sim_write(ctx, dut.bus, 0, 0) #Disable
                
            # Received 4 responses
            assert await Bus.sim_read(ctx, dut.bus, 7) == 0 # ACK
            assert await Bus.sim_read(ctx, dut.bus, 5) == 10
            assert await Bus.sim_read(ctx, dut.bus, 7) == 0 # ACK
            assert await Bus.sim_read(ctx, dut.bus, 5) == 11
            assert await Bus.sim_read(ctx, dut.bus, 7) == 0 # ACK
            assert await Bus.sim_read(ctx, dut.bus, 5) == 12
            assert await Bus.sim_read(ctx, dut.bus, 7) == 0 # ACK
            assert await Bus.sim_read(ctx, dut.bus, 5) == 13
            
        async def i2c_process(ctx):
            while not response.last():
                sda = ctx.get(dut.sda)
                scl = ctx.get(dut.scl)
                response.get(ctx, sda, scl, dut.sda_in)
                await ctx.tick()
                
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_testbench(bus_process)
        sim.add_testbench(i2c_process)
        
        with sim.write_vcd("bench/serial_test.vcd"):
            sim.run_until(1000 * 1e-8)
            
class TestSerialBusBridge(unittest.TestCase):
    def test_rw_short(self):
        dut = SerialToWishbone()
        
        async def command_process(ctx):
            await Stream.sim_write(ctx, dut.command, ord('w'))
            await Stream.sim_write(ctx, dut.command, 1)
            await Stream.sim_write(ctx, dut.command, 11)
            
            # Write reply
            assert await Stream.sim_get(ctx, dut.reply) == ord('W')
            assert await Stream.sim_get(ctx, dut.reply) == 0
            assert await Stream.sim_get(ctx, dut.reply) == 0
            assert await Stream.sim_get(ctx, dut.reply) == 0
            assert await Stream.sim_get(ctx, dut.reply) == 1
            assert await Stream.sim_get(ctx, dut.reply) == 10 # EOL
            
            await Stream.sim_write(ctx, dut.command, ord('r'))
            await Stream.sim_write(ctx, dut.command, 1)
            
            # Read reply
            assert await Stream.sim_get(ctx, dut.reply) == ord('R')
            assert await Stream.sim_get(ctx, dut.reply) == 0
            assert await Stream.sim_get(ctx, dut.reply) == 0
            assert await Stream.sim_get(ctx, dut.reply) == 0
            assert await Stream.sim_get(ctx, dut.reply) == 11
            assert await Stream.sim_get(ctx, dut.reply) == 10 # EOL
            
        async def bus_process(ctx):
            device = MockBusDevice()
            
            while True:
                await device.run(ctx, dut.produce)
                
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_process(command_process)
        sim.add_testbench(bus_process)
        
        with sim.write_vcd("bench/serial2bus.vcd"):
            sim.run_until(1000*1e-8)
        
            
class TestUart(unittest.TestCase):
    def test_uart_tx(self):
        dut = UartTx(period = 10, parity = True)
        
        period = 10
        half = 5
        
        async def process(ctx):
            await Stream.sim_write(ctx, dut.consume, 0b10101001)
            await Stream.sim_write(ctx, dut.consume, 0b00110001)
            
        async def uart_get(ctx, *args):
            expect = list(args)
            await ctx.tick().until(dut.tx == 0)
            print("Got start bit")
            tx, = await ctx.tick().sample(dut.tx).repeat(half)
            assert tx == 0
            
            for i in range(len(expect)):
                tx, = await ctx.tick().sample(dut.tx).repeat(period)
                assert tx == expect[i]
            
        async def uart_process(ctx):
            
            await uart_get(ctx, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1)
            await uart_get(ctx, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1)
            
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_process(process)
        sim.add_process(uart_process)
        
        with sim.write_vcd("bench/uart_tx.vcd"):
            sim.run_until(1000*1e-8)
            
    def test_uart_rx(self):
        dut = UartRx(period = 10, parity = True)
        
        period = 10
        
        async def process(ctx):
            assert await Stream.sim_get(ctx, dut.produce) == 0b10101001
            assert await Stream.sim_get(ctx, dut.produce) == 0b10010001
            
        async def uart_process(ctx):
            data = [
                1, 1, 1, 1, #idle
                0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, # Word 1 with start, parity, stop
                0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, # Word 2 with start, parity, stop
                1, 1, 1, 1 # Idle
            ]
            for d in data:
                ctx.set(dut.rx, d)
                await ctx.tick().repeat(period)
                
        sim = Simulator(dut)
        sim.add_clock(1e-8)
        sim.add_process(process)
        sim.add_process(uart_process)
        
        with sim.write_vcd("bench/uart_rx.vcd"):
            sim.run_until(1000*1e-8)
            
if __name__ == "__main__":
    unittest.main()
    
    
                