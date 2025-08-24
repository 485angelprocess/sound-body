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

from infra.switch import AddressSwitch, SwitchPortDef, BusSwitch

from core.cpu import RiscCore

from build_module import build

class RiscProject(wiring.Component):
    def __init__(self, normally_on=False, uart_period=868):
        self.uart_period = uart_period
        self.normally_on = normally_on
    
        super().__init__({
            "axi": Out(signature.AxiLite(32, 32)), # AXI
            "tx": Out(1),
            "rx": In(1),
            "periph_resetn": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        ######################
        # UART ###############
        ######################
        # UART In/Out
        m.submodules.uart_tx = uart_tx = UartTx(period=self.uart_period)
        m.submodules.uart_rx = uart_rx = UartRx(period=self.uart_period)
        
        m.d.comb += [
            self.tx.eq(uart_tx.tx),
            uart_rx.rx.eq(self.rx)
        ]
        
        # UART Controller
        m.submodules.bridge = bridge = SerialToWishbone()
        
        wiring.connect(m, uart_tx.consume, bridge.reply)
        wiring.connect(m, uart_rx.produce, bridge.command)
        
        
        # First 256 addresses are internal
        m.submodules.bridge_sw = bridge_sw = AddressSwitch(split=256)
        
        wiring.connect(m, bridge_sw.consume, bridge.produce)
        
        # Reset external devices
        m.d.comb += [
            self.periph_resetn.eq(bridge.soft_reset)
        ]
        
        core_reset = Signal()
        
        ###############
        # RISC-V Core #
        ###############
        m.submodules.core = core = ResetInserter(core_reset)(RiscCore(has_mul=False, normally_on=self.normally_on))
        
        m.d.comb += core_reset.eq(core.debug_reset)
        
        # Control from uart
        wiring.connect(m, bridge_sw.a, core.debug)
        
        # Core access to registers/data
        m.submodules.bus_switch = bus_switch = ResetInserter(core_reset)(AddressSwitch(split=256))
        
        wiring.connect(m, bus_switch.consume, core.bus)
        # TEMP: Can only write to uart
        wiring.connect(m, bus_switch.a, bridge.bus)
        
        ###########################
        # Connect to AXI devices ##
        ###########################
        # Wishbone switch
        m.submodules.switch = main_switch = BusSwitch([SwitchPortDef(32, 32)], num_inputs=3)
        m.submodules.to_axi = to_axi = WishboneToAxi()
        
        # Program memory access
        wiring.connect(m, main_switch.c_00, core.prog)
        # Memory acces
        wiring.connect(m, main_switch.c_01, bus_switch.b)
        # DMA from Uart
        wiring.connect(m, main_switch.c_02, bridge_sw.b)
        
        wiring.connect(m, to_axi.wish, main_switch.p_00)
        wiring.connect(m, to_axi.axi, wiring.flipped(self.axi))
        
        # Error bus
        wiring.connect(m, to_axi.error, bridge.error)
        
        return m
        
if __name__ == "__main__":
    rp = RiscProject()

    build(rp, "risc_project")