import serial
import argparse
import time

class UartException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        
def to_word(m, size = 4):
    """
    Go from string to bytes
    """
    d = int(m)
    
    result = list()
    for i in range(size):
        result.append((d >> ( 8*(size - i - 1) )) & 0xFF)
    return bytes(result)

class Monitor(object):
    def __init__(self, port = "COM15", baud = 9600):
        self.port = port
        
        self.s = serial.Serial(port, 9600, timeout = 0.1)
        
    def write(self, msg):
        print("Sending {}".format(msg))
        self.s.write(msg)
        
    def read(self):
        r = self.s.read()
        return r
        
    def rw(self, msg):
        self.write(msg)
        response = list()
        for _ in range(10):
            r = self.read()
            if len(r) > 0:
                response.append(r)
            else:
                if len(response) > 0:
                    if response[0][0] == ord('%'):
                        raise UartException("Parsing error")
                #print(response)
                return response
        #print(response)
        return response
        
    def prompt(self):
        msg = input(">")
        
        if len(msg) > 0:
            if msg.startswith("I"):
                self.write("I".encode("ascii"))
            elif msg.startswith("W"):
                msg = msg.split(" ")
                print(msg)
                code = "W".encode("ascii")
                self.write(code)
                self.write(to_word(msg[1]))
                self.write(to_word(msg[2]))
            elif msg.startswith("w"):
                msg = msg.split(" ")
                code = "w".encode("ascii")
                addr = to_word(msg[1], size=1)
                data = to_word(msg[2], size=1)
                self.write(code)
                self.write(addr)
                self.write(data)
            elif msg.startswith("R"):
                msg = msg.split(" ")
                code = "R".encode("ascii")
                addr = to_word(msg[1])
                self.write(code)
                self.write(addr)
            elif msg.startswith("r"):
                msg = msg.split(" ")
                code = "r".encode("ascii")
                addr = to_word(msg[1], size=1)
                self.write(code)
                self.write(addr)
            else:
                self.write(msg.encode("ascii"))
            
        for _ in range(10):
            r = self.read()
            if len(r) > 0:
                print(r, end = '')
        
        print("")
        
    def get_ack(self, address):
        self.rw([ord('w'), 2, 1]) # start flag
        self.rw([ord('w'), 1, address]) # Write data
        
        print("Num writes: {}".format(self.rw([ord('r'), 4])[1][0])) # Get number of writes
        
        self.rw([ord('w'), 0, 1]) # Enable
        time.sleep(0.2)
        n_reads = self.rw([ord('r'), 6])[1][0]
        print("Num reads available: {}".format(n_reads))
        assert  n_reads == 0x01 # number of reads
        
        self.rw([ord('w'), 0, 0]) # Disable
        
        # Get response
        if self.rw([ord('r'), 7])[1][0] == 0: # ACK
            print("Found device at address {}", address)
        print("Data response: {}".format(self.rw([ord('r'), 5]))) # data
        
    def reset_i2c(self, period = [0, 0, 0, 250]):
        self.rw([ord('x')]) # reset
        self.rw('I'.encode('ascii'))
        self.rw([ord('W'), 0, 0, 0, 8] + period)
        
        self.rw([ord('w'), 3, 1]) # Write
        
    def i2c_scan(self, address_start, address_stop):
        self.reset_i2c()
        
        a = address_start
        while True:
            print(a)
            
            try:
                self.get_ack(a)
                a += 1
            except UartException as e:
                # Reset
                print("Resetting")
                self.reset_i2c()
                
            if a >= address_stop:
                return
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "Serial tests")
    
    parser.add_argument("port", help = "COMPORT")
    parser.add_argument("--address", "-a", type = int, default = 0b01110110, help = "I2C address")

    args = parser.parse_args()

    m = Monitor(port = args.port)
    
    #m.i2c_scan(110, 120)
    
    # Interactive
    while True:
        m.prompt()