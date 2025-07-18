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

from infra.switch import AddressSwitch

from core.cpu import RiscCore

from build_module import build

class RiscProject(wiring.Component):
    def __init__(self):
        super().__init__({
            "axi": Out(signature.AxiLite(32, 32)), # Memory access
            "prog": Out(signature.AxiLite(32, 32)), # Program memory
            "direct": Out(signature.AxiLite(32, 32)),
            "tx": Out(1),
            "rx": In(1),
            "periph_resetn": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        # UART In/Out
        m.submodules.uart_tx = uart_tx = UartTx()
        m.submodules.uart_rx = uart_rx = UartRx()
        
        m.d.comb += [
            self.tx.eq(uart_tx.tx),
            uart_rx.rx.eq(self.rx)
        ]
        
        # UART Controller
        m.submodules.bridge = bridge = SerialToWishbone()
        
        wiring.connect(m, uart_tx.consume, bridge.reply)
        wiring.connect(m, uart_rx.produce, bridge.command)
        
        # Connect uart controller to external axi devices
        m.submodules.bridge_to_axi = bridge_to_axi = WishboneToAxi()
        
        # First 256 addresses are internal
        m.submodules.bridge_sw = bridge_sw = AddressSwitch(split=256)
        
        wiring.connect(m, bridge_sw.consume, bridge.produce)
        
        wiring.connect(m, bridge_to_axi.wish, bridge_sw.b)
        wiring.connect(m, bridge_to_axi.axi, wiring.flipped(self.direct))
        
        # Reset external devices
        m.d.comb += [
            self.periph_resetn.eq(bridge.soft_reset)
        ]
        
        # RISC-V Core
        m.submodules.core = core = RiscCore(has_mul=False)
        
        # Control from uart
        wiring.connect(m, bridge_sw.a, core.debug)
        
        # Bridge to axi
        
        
        return m
        
if __name__ == "__main__":
    rp = RiscProject()

    build(rp, "risc_project")