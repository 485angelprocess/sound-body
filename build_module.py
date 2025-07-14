import argparse

from amaranth import *
from amaranth.lib import wiring

from amaranth.back import verilog

from ser.uart import UartTx, UartRx
from ser.serial_to_wishbone import SerialToWishbone
from ser.i2c import I2CTop

from axi.script import AxiScript, AxiCommand

from audio.square import SquareGenerator

def build(m, name, dir = "build", ext = "v", ports = None):
    with open("{}/{}.{}".format(dir, name, ext), 'w') as f:
        if ports is None:
            f.write(verilog.convert(m, name).replace("__", "_"))
        else:
            f.write(verilog.convert(m, name, ports = ports).replace("__", "_"))
    print("Write {}/{}.{}".format(dir, name, ext))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "Build verilog modules")
    
    parser.add_argument("-u", "--uart", action = "store_true", help = "Build uart modules")
    parser.add_argument("-p", "--uart_period", type = int, default = 10417, help = "Uart period")
    parser.add_argument("-s", "--serial", action = "store_true", help = "Build serial modules")
    parser.add_argument("--serial_demo", action = "store_true", help = "Build serial demo")
    parser.add_argument("--i2s", action = "store_true", help = "Build i2s stuff")
    parser.add_argument("-a", "--all", action = "store_true", help = "Build all modules")
    
    args = parser.parse_args()
    
    if args.uart or args.serial or args.all:
        build(UartTx(period = args.uart_period, parity = False), "uart_tx")
        build(UartRx(period = args.uart_period, parity = False), "uart_rx")
    if args.serial or args.all:
        build(SerialToWishbone(), "serial_to_wishbone")
        build(I2CTop(max_period = 1024), "i2c")
        
    if args.i2s:
        build(AxiScript(
            AxiCommand(0x20, 4), # Set divider
            AxiCommand(0x08, 0x01),
            AxiCommand(0x30, 0x01) # Set channel output
        ), "i2s_startup")
        
        build(SquareGenerator(period = 10), "square_generator")
        
    if args.serial_demo:
        ########################
        ## UART loopback #######
        ########################
        m = Module()
        
        m.submodules.uart_tx = tx = UartTx(period = args.uart_period)
        m.submodules.uart_rx = rx = UartRx(period = args.uart_period)
        
        wiring.connect(m, tx.consume, rx.produce)
        
        build(m, "uart_loopback_demo", ports = [tx.tx, rx.rx])
        
        ########################
        ## serial to bridge ####
        ########################
        m = Module()
        
        m.submodules.uart_tx = tx = UartTx(period = args.uart_period, parity = False)
        m.submodules.uart_rx = rx = UartRx(period = args.uart_period, parity = False)
        
        m.submodules.bridge = bridge = SerialToWishbone()
        
        wiring.connect(m, tx.consume, bridge.reply)
        wiring.connect(m, rx.produce, bridge.command)
        
        build(m, "serial_bridge", ports = [tx.tx, rx.rx])
        
        ###############################
        ## Serial 2 bridge with i2c ###
        ###############################
        m = Module()
        
        m.submodules.uart_tx = tx = UartTx(period = args.uart_period, parity = False)
        m.submodules.uart_rx = rx = UartRx(period = args.uart_period, parity = False)
        
        m.submodules.bridge = bridge = SerialToWishbone()
        
        m.submodules.i2c = i2c = I2CTop(max_period = 1024)
        
        wiring.connect(m, tx.consume, bridge.reply)
        wiring.connect(m, rx.produce, bridge.command)
        wiring.connect(m, bridge.produce, i2c.bus)
        
        build(m, "serial_demo", ports = [
                    tx.tx, 
                    rx.rx,
                    bridge.soft_reset,
                    i2c.sda,
                    i2c.sda_en,
                    i2c.sda_in,
                    i2c.scl])