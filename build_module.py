import argparse

from amaranth.back import verilog

from serial.uart import UartTx, UartRx

def build(m, name, dir = "build", ext = "v"):
    with open("{}/{}.{}".format(dir, name, ext), 'w') as f:
        f.write(verilog.convert(m, name).replace("__", "_"))
    print("Write {}/{}.{}".format(dir, name, ext))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "Build verilog modules")
    
    parser.add_argument("-u", "--uart", action = "store_true", help = "Build uart modules")
    parser.add_argument("-p", "--uart_period", type = int, default = 10417, help = "Uart period")
    parser.add_argument("-s", "--serial", action = "store_true", help = "Build serial modules")
    parser.add_argument("-a", "--all", action = "store_true", help = "Build all modules")
    
    args = parser.parse_args()
    
    if args.uart or args.serial or args.all:
        build(UartTx(period = args.uart_period, parity = False), "uart_tx")
        build(UartRx(period = args.uart_period, parity = False), "uart_rx")