"""
I2c driver
"""
from infra.signature import *

from amaranth import *
from amaranth.lib import wiring, fifo, enum
from amaranth.lib.wiring import In, Out

class I2CRegister(enum.Enum):
    ENABLE = 0
    WRITE_DATA = 1 # Write word to buffer WO
    WRITE_START = 2 # Write if this word is the start
    DATA_EN = 3
    WRITE_LEN = 4  # Number of words in buffer RO
    READ_DATA = 5 # Read word from buffer
    READ_LEN = 6 # Number of words to read
    READ_ACK = 7
    PERIOD = 8
    
class I2CController(wiring.Component):
    """
    Bus controlled unit
    """
    def __init__(self):
        super().__init__({
            "bus": In(Bus(4, 32)),
            
            # Control signals
            "ctl_period": In(32),
            "wlen": In(32),
            "rlen": In(32),
            "enable": Out(1),
            
            # write /read from buffers
            "write_data": Out(8),
            "start": Out(1),
            "dat_en": Out(1),
            "write_valid": Out(1),
            "write_ready": In(1),
            
            "read_data": In(8),
            "read_ack": In(1),
            "read_valid": In(1),
            "read_ready": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        period = Signal(12, init = 100)
        
        m.d.comb += self.ctl_period.eq(period)
        
        with m.If(self.bus.cyc & self.bus.stb):
            with m.If(self.bus.w_en):
                # Write to bus
                with m.If(self.bus.addr == I2CRegister.WRITE_DATA):
                    m.d.comb += self.write_valid.eq(1)
                    m.d.comb += self.bus.ack.eq(1) # Prevent lock, could wait for fifo but that's less likely case i think
                    # Could put error flag for case where fifo is full
                with m.Else():
                    m.d.comb += self.bus.ack.eq(1)
                
                with m.Switch(self.bus.addr):
                    with m.Case(I2CRegister.ENABLE):
                        # Enable/disable driver
                        m.d.sync += self.enable.eq(self.bus.w_data)
                    with m.Case(I2CRegister.WRITE_DATA):
                        # Write data, loads to fifo
                        m.d.comb += self.write_data.eq(self.bus.w_data)
                        m.d.sync += self.start.eq(0) # Clear start flag
                    with m.Case(I2CRegister.WRITE_START):
                        # Write start flag
                        m.d.sync += self.start.eq(self.bus.w_data)
                    with m.Case(I2CRegister.PERIOD):
                        # Set I2C period
                        m.d.sync += period.eq(self.bus.w_data)
                    with m.Case(I2CRegister.DATA_EN):
                        m.d.sync += self.dat_en.eq(self.bus.w_data)
                    with m.Default():
                        pass
            with m.Else():
                with m.If(self.bus.addr == I2CRegister.READ_DATA):
                    # Read from buffer
                    m.d.comb += self.read_ready.eq(1)
                    m.d.comb += self.bus.ack.eq(self.read_valid)
                with m.Else():
                    m.d.comb += self.bus.ack.eq(1)
                    
        # Read data
        with m.Switch(self.bus.addr):
            with m.Case(I2CRegister.ENABLE):
                m.d.comb += self.bus.r_data.eq(self.enable)
            with m.Case(I2CRegister.WRITE_DATA):
                pass
            with m.Case(I2CRegister.WRITE_START):
                m.d.comb += self.bus.r_data.eq(self.start)
            with m.Case(I2CRegister.WRITE_LEN):
                m.d.comb += self.bus.r_data.eq(self.wlen)
            with m.Case(I2CRegister.READ_DATA):
                # Does more than this
                m.d.comb += self.bus.r_data.eq(self.read_data)
            with m.Case(I2CRegister.READ_ACK):
                m.d.comb += self.bus.r_data.eq(self.read_ack)
            with m.Case(I2CRegister.READ_LEN):
                m.d.comb += self.bus.r_data.eq(self.rlen)
            with m.Case(I2CRegister.DATA_EN):
                m.d.comb += self.bus.r_data.eq(self.dat_en)
            with m.Case(I2CRegister.PERIOD):
                m.d.comb += self.bus.r_data.eq(period)
        
        return m

class I2CSend(wiring.Component):
    """
    I2c controller
    """
    def __init__(self, max_period = 1024, buffer_size = 16):
        self.buffer_size = buffer_size
        self.max_period = max_period
        
        super().__init__({
            "enable": In(1),
            
            "ctl_period": In(range(self.max_period)),
            
            "write_data": In(8),
            "start": In(1),
            "write_data_en": In(1),
            "write_valid": In(1),
            "write_ready": Out(1),
            
            "read_data": Out(8),
            "ack": Out(1),
            "read_ready": In(1),
            "read_valid": Out(1),
            
            "wlen": Out(range(self.buffer_size)),
            "rlen": Out(range(self.buffer_size)),
            
            "clk_en": Out(1),
            "dat_en": Out(1),
            "data": Out(1),
            "ready": In(1),
            "valid": Out(1),
            "period": Out(range(self.max_period)),
            
            "i2c_read_data": In(1),
            "i2c_read_en": In(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        #################################
        ## Write buffer #################
        #################################
        wbuffer = m.submodules.wbuffer = fifo.SyncFIFO(width = 10, depth = self.buffer_size)
        
        m.d.comb += self.wlen.eq(wbuffer.level)
        
        # Write to write buffer
        m.d.comb += [
            wbuffer.w_data[0:8].eq(self.write_data),
            wbuffer.w_data[-1].eq(self.start),
            wbuffer.w_data[-2].eq(self.write_data_en),
            wbuffer.w_en.eq(self.write_valid),
            self.write_ready.eq(wbuffer.w_rdy)
        ]
        
        #################################
        ## controller ###################
        #################################
        start = Signal()
        write_counter = Signal(range(8))
        
        m.d.comb += start.eq(wbuffer.r_data[-1])
        
        m.d.comb += self.period.eq(self.ctl_period)
        
        read_counter = Signal(range(9), init = 8)
        
        # Run i2c
        with m.FSM() as fsm:
            with m.State("Idle"):
                with m.If(wbuffer.r_rdy & self.enable):
                    m.d.sync += read_counter.eq(8)
                    m.d.sync += write_counter.eq(7)
                    with m.If(start):
                        m.next = "Start"
                    with m.Else():
                        m.next = "Data"
            with m.State("Start"):
                # Write start condition
                m.d.comb += self.dat_en.eq(1)
                m.d.comb += self.clk_en.eq(0)
                m.d.comb += self.data.eq(1) # Start condition
                m.d.comb += self.valid.eq(1)
                # May make this shorter
                with m.If(self.ready):
                    m.next = "StartB"
            with m.State("StartB"):
                m.d.comb += self.dat_en.eq(1)
                m.d.comb += self.clk_en.eq(0)
                m.d.comb += self.data.eq(0)
                m.d.comb += self.valid.eq(1)
                with m.If(self.ready):
                    m.d.sync += write_counter.eq(7)
                    m.next = "Data"
            with m.State("Data"):
                # Write or read word of data
                m.d.comb += self.dat_en.eq(wbuffer.r_data[-2])
                m.d.comb += self.clk_en.eq(1)
                m.d.comb += self.data.eq(wbuffer.r_data.bit_select(write_counter, 1))
                m.d.comb += self.valid.eq(1)
                with m.If(self.ready):
                    with m.If(write_counter == 0):
                        # Read next value from write fifo
                        # TODO maybe add explicit stop
                        m.d.sync += write_counter.eq(7)
                        m.next = "Ack"
                    with m.Else():
                        m.d.sync += write_counter.eq(write_counter - 1)
            with m.State("Ack"):
                # Get ack bit
                m.d.comb += self.dat_en.eq(0)
                m.d.comb += self.clk_en.eq(1)
                m.d.comb += self.valid.eq(1)
                with m.If(self.ready):
                    m.next = "GetAck"
            with m.State("GetAck"):
                with m.If(self.i2c_read_en):
                    m.d.comb += wbuffer.r_en.eq(1)
                    with m.If(wbuffer.level > 1):
                        m.next = "Idle"
                    with m.Else():
                        m.d.sync += write_counter.eq(1)
                        m.next = "Stop"
            with m.State("Stop"):
                m.d.comb += self.dat_en.eq(1)
                m.d.comb += self.clk_en.eq(0)
                m.d.comb += self.valid.eq(1)
                with m.If(write_counter == 1):
                    m.d.comb += self.data.eq(0)
                    with m.If(self.ready):
                        m.next = "Idle"
                with m.Else():
                    m.d.comb += self.data.eq(1)
                    with m.If(self.ready):
                        m.d.sync += write_counter.eq(0)
                
        ##############################
        ## Read buffer ###############
        ##############################
        rbuffer = m.submodules.rbuffer = fifo.SyncFIFO(width = 9, depth = self.buffer_size)
                
        m.d.comb += self.rlen.eq(rbuffer.level)
                
        
        read_register = Signal(9)
        read_flag = Signal()
        
        m.d.comb += rbuffer.w_data.eq(read_register)
        
        with m.If(read_flag):
            m.d.sync += read_flag.eq(0)
            m.d.comb += rbuffer.w_en.eq(1)
            m.d.sync += read_register.eq(0)
            m.d.sync += read_counter.eq(8)
        
        with m.If(self.i2c_read_en):
            m.d.sync += read_register.bit_select(read_counter, 1).eq(self.i2c_read_data)
            
            with m.If(read_counter == 0):
                m.d.sync += read_flag.eq(1)
            with m.Else():
                m.d.sync += read_counter.eq(read_counter - 1)
            
        m.d.comb += [
            self.ack.eq(rbuffer.r_data[0]),
            self.read_data.eq(rbuffer.r_data[1:9]),
            self.read_valid.eq(rbuffer.r_rdy),
            rbuffer.r_en.eq(self.read_ready)
        ]
        
        return m

class I2COut(wiring.Component):
    """
    Drive serial lines
    """
    def __init__(self, max_period = 1024):
        self.max_period = max_period
    
        super().__init__({
            # Input
            "clk_en": In(1),
            "dat_en": In(1),
            "data": In(1),
            "ready": Out(1),
            "valid": In(1),
            "period": In(range(max_period)),
            # Data
            "read_data": Out(1),
            "read_valid": Out(1),
            #I2C interface
            "sda": Out(1),
            "sda_en": Out(1),
            "sda_in": In(1),
            "scl": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        counter = Signal(range(self.max_period))
        half_period = Signal(range(self.max_period))
        
        clk_en = Signal()
        dat_en = Signal()
        
        # Rising edge
        with m.If(clk_en):
            m.d.comb += self.scl.eq(counter < half_period)
        with m.Else():
        # clock disabled
            m.d.comb += self.scl.eq(1)
            
        # Read data from line
        m.d.comb += self.read_valid.eq((clk_en) & (counter == half_period - 2))
        m.d.comb += self.read_data.eq(self.sda_in)
            
        data = Signal()
            
        # send data out
        with m.If(dat_en):
            m.d.comb += self.sda_en.eq(1)
            m.d.comb += self.sda.eq(data)
        with m.Else():
            m.d.comb += self.sda.eq(1)
            m.d.comb += self.sda_en.eq(0)
        
        with m.FSM():
            with m.State("Idle"):
                m.d.comb += self.ready.eq(1)
                with m.If(self.valid):
                    
                    m.d.sync += clk_en.eq(self.clk_en)
                    m.d.sync += dat_en.eq(self.dat_en)
                    
                    m.d.sync += counter.eq(self.period)
                    m.d.sync += half_period.eq(self.period >> 1)
                    m.d.sync += data.eq(self.data) # get data
                    m.next = "Send"
                with m.Else():
                    # Disable clock and data if no signal immediately available
                    m.d.sync += clk_en.eq(0)
                    m.d.sync += dat_en.eq(0)
            with m.State("Send"):
                m.d.sync += counter.eq(counter - 1)
                with m.If(counter == 1):
                    m.next = "Idle"
        
        return m
        
class I2CTop(wiring.Component):
    def __init__(self, max_period = 1024, buffer_size = 16):
        self.max_period = max_period
        self.buffer_size = buffer_size
        
        super().__init__({
            "bus": In(Bus(4, 32)),
            "sda": Out(1),
            "sda_en": Out(1),
            "sda_in": In(1),
            "scl": Out(1)
        })
        
    def elaborate(self, platform):
        m = Module()
        
        # Output device
        m.submodules.out = out = I2COut(self.max_period)
        
        # Output to i2c out
        m.d.comb += [
            self.sda.eq(out.sda),
            self.sda_en.eq(out.sda_en),
            out.sda_in.eq(self.sda_in),
            self.scl.eq(out.scl)
        ]
        
        # Middleware
        m.submodules.send = send = I2CSend(self.max_period, self.buffer_size)
        
        # i2c out connect to middle ware
        m.d.comb += [
            # Write out
            out.period.eq(send.period),
            out.clk_en.eq(send.clk_en),
            out.dat_en.eq(send.dat_en),
            out.data.eq(send.data),
            send.ready.eq(out.ready),
            out.valid.eq(send.valid),
            
            # Read in
            send.i2c_read_data.eq(out.read_data),
            send.i2c_read_en.eq(out.read_valid)
        ]
        
        # Bus controller
        m.submodules.controller = controller = I2CController()
        
        # Connect to top level
        wiring.connect(m, controller.bus, wiring.flipped(self.bus))
        
        # Control signals
        m.d.comb += [
            send.ctl_period.eq(controller.ctl_period),
            controller.wlen.eq(send.wlen),
            controller.rlen.eq(send.rlen),
            send.enable.eq(controller.enable)
        ]
        
        # Buffer write
        m.d.comb += [
            send.write_data.eq(controller.write_data),
            send.start.eq(controller.start),
            send.write_data_en.eq(controller.dat_en),
            send.write_valid.eq(controller.write_valid),
            controller.write_ready.eq(send.write_ready)
        ]
        
        # Buffer read
        m.d.comb += [
            controller.read_data.eq(send.read_data),
            controller.read_ack.eq(send.ack),
            controller.read_valid.eq(send.read_valid),
            send.read_ready.eq(controller.read_ready)
        ]
        
        return m