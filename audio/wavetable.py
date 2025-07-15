"""
Wavetable worker for audio frequency oscillator
"""
from signature import Bus
from datatype import Float

class WavetableReg(enum.Enum):
    START = 0 # Value in memory to start from
    STOP  = 1 # Value in memory to stop at
    PHASE = 2 # Offset from start
    AMPL  = 3 # Amplitude
    STRIDE     = 4 # How fast to step through values
    DOWNSAMPLE = 5 # How much to downsample stride
    RESULT = 6 # Read from  wavetable
    ENABLE = 7
    
    # TODO add stream enable and stream dest
    # Could go to audio buffer etc.
    
# TODO consider adding stream out?
# Only if we are putting all things
# outside of cpu thread
class WavetableGen(enum.Enum):
    def __init__(self):
        super().__init__({
            "bus": In(Bus(4, 32)),
            "mem": Out(Bus(32, 32)) # Read from memory
        })
        
    def elaborate(self, platform):
        m = Module()
        
        start = Signal(32)
        stop = Signal(32)
        phase = Signal(32)
        
        ampl = Signal(Float)
        stride = Signal(32)
        downsample = Signal(3)
        
        counter = Signal(64)
        index = Signal(32)
        
        m.d.comb += index.eq(counter >> downsample)
        
        addr = Signal(32)
        
        m.d.comb += addr.eq(
            index + start
        )
        
        m.d.comb += self.mem.addr.eq(addr)
        
        last = Signal()
        
        with m.If(index >= stop):
            m.d.comb += last.eq(1)
        
        enable = Signal()
        result = Signal(Float)
        next = Signal()
        initial = Signal()
        
        # Bus control
        with m.If(self.bus.cyc & self.bus.stb):
            m.d.comb += self.bus.ack.eq(1)
            with m.If(self.bus.w_en):
                # Write to registers
                with m.Switch(self.bus.addr):
                    with m.Case(WavetableReg.START):
                        m.d.sync += start.eq(self.bus.w_data)
                    with m.Case(WavetableReg.STOP):
                        m.d.sync += stop.eq(self.bus.w_data)
                    with m.Case(WavetableReg.PHASE):
                        m.d.sync += phase.eq(self.bus.w_data)
                    with m.Case(WavetableReg.AMPL):
                        m.d.sync += ampl.eq(self.bus.w_data)
                    with m.Case(WavetableReg.STRIDE):
                        m.d.sync += stride.eq(self.bus.w_data)
                    with m.Case(WavetableReg.DOWNSAMPLE):
                        m.d.sync += downsample.eq(self.bus.w_data)
                    with m.Case(WavetableReg.ENABLE):
                        m.d.sync += enable.eq(self.bus.w_data)
                        m.d.comb += initial.eq(1)
                        # Reset position
                        m.d.sync += counter.eq(phase << downsample)
            with m.Else():
                # Read from registers
                with m.Switch(self.bus.addr):
                    with m.Case(WavetableReg.START):
                        m.d.comb += self.bus.r_data.eq(start)
                    with m.Case(WavetableReg.STOP):
                        m.d.comb += self.bus.r_data.eq(stop)
                    with m.Case(WavetableReg.PHASE):
                        m.d.comb += self.bus.r_data.eq(phase)
                    with m.Case(WavetableReg.AMPL):
                        m.d.comb += self.bus.r_data.eq(ampl)
                    with m.Case(WavetableReg.STRIDE):
                        m.d.comb += self.bus.r_data.eq(stride)
                    with m.Case(WavetableReg.DOWNSAMPLE):
                        m.d.comb += self.bus.r_data.eq(downsample)
                    with m.Case(WavetableReg.RESULT):
                        # Get next value from wavetable and then
                        # calculate the next value
                        m.d.comb += self.bus.r_data.eq(result)
                        m.d.sync += next.eq(1)
                    with m.Case(WavetableReg.ENABLE):
                        m.d.comb += self.bus.r_data.eq(enable)
        
        a = Signal(Float)
        b = Signal(Float)
        fraction = Signal(24)
        ampfraction = Signal(24)
        
        fraction_product = Signal(48)
        
        m.d.comb += ampfraction.eq(
            Cat(Const(1, 1), ampl.fraction)
        )
        
        # Read through wavetable
        with m.FSM():
            with m.State("Idle"):
                with m.If((enable & next) | initial):
                    # Get next index to read from
                    
                    m.next = "Read"
            with m.State("Read"):
                # TODO read into fifo so reads are concurrent as much as possible
                # Although can be handled by cache outside module
                m.d.comb += self.mem.cyc.eq(1)
                m.d.comb += self.mem.stb.eq(1)
                with m.If(self.mem.ack):
                    with m.If(initial):
                        pass # Prevent race condition when trying to reset 
                    with m.Elif(last):
                        m.d.sync += counter.eq(0)
                    with m.Else():
                        m.d.sync += counter.eq(counter + stride)
                
                    # Scale output of float value
                    m.d.sync += a.eq(self.mem.r_data)
                    m.d.sync += next.eq(0)
                    # TODO write reusable floating pointmultpiler
                    m.next = "A"
            with m.State("A"):
                # Get exponent, sign and copy fraction
                m.d.sync += working.exponent.eq(a.exponent + ampl.exponent - 127)
                m.d.sync += working.sign.eq(a.sign ^ ampl.sign)
                m.d.sync += fraction.eq(Cat(1, 1), working.fraction)
                m.next = "B"
            with m.State("B"):
                # Multiplication
                m.d.sync += fraction_product.eq(
                    fraction * ampfraction
                )
                m.next = "C"
            with m.State("C"):
                # Rounding
                # TODO
                
                with m.If(next):
                    m.next = "Read"
                with m.Else():
                    m.next = "Idle"
        
        return m