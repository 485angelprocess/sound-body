"""
Build RISC-V core with bus interfaces
"""
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from infra import signature

from axi.wish_to_axi import WishboneToAxi
from ser.serial_to_wishbone import SerialToWishbone
from ser.uart import UartTx, UartRx

from build_module import build

class RiscProject(wiring.Component):
    def __init__(self):
        super().__init__({
            "axi": Out(signature.AxiLite(32, 32)), # Memory access
            "prog": Out(signature.AxiLite(32, 32)), # Program memory
            "direct": Out(signature.AxiLite(32, 32)),
            "tx": Out(1),
            "rx": In(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        m.submodules.uart_tx = uart_tx = UartTx()
        m.submodules.uart_rx = uart_rx = UartRx()
        
        m.submodules.bridge = bridge = SerialToWishbone()
        
        m.d.comb += [
            self.tx.eq(uart_tx.tx),
            uart_rx.rx.eq(self.rx)
        ]
        
        wiring.connect(m, uart_tx.consume, bridge.reply)
        wiring.connect(m, uart_rx.produce, bridge.command)
        
        m.submodules.bridge_to_axi = bridge_to_axi = WishboneToAxi()
        
        wiring.connect(m, bridge_to_axi.wish, bridge.produce)
        wiring.connect(m, bridge_to_axi.axi, wiring.flipped(self.direct))
        
        return m
        
if __name__ == "__main__":
    rp = RiscProject()

    build(rp, "risc_project")