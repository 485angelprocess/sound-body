import serial
import argparse

class Monitor(object):
    def __init__(self, port = "COM15", baud = 9600):
        self.port = port
        
        self.s = serial.Serial(port, 9600, timeout = 0.1)
        
    def write(self, msg):
        #print("Sending {}".format(msg))
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
                print(response)
                return response
        #print(response)
        return response
        
    def prompt(self):
        msg = input(">").encode('ascii')
        
        if len(msg) > 0:
            self.write(msg)
            
        for _ in range(10):
            r = self.read()
            if len(r) > 0:
                print(r, end = '')
        
        print("")
        
    def i2c_scan(self, address_start, address_stop):
        self.rw([ord('x')]) # reset
        self.rw('I'.encode('ascii'))
        self.rw([ord('W'), 0, 0, 0, 8, 0xFF, 0xFF, 0xFF, 0xFF])
        
        for a in range(address_start, address_stop):
            self.rw([ord('w'), 3, 1]) # Write
            self.rw([ord('w'), 2, 1]) # start flag
            self.rw([ord('w'), 1, a]) # Write data
            
            self.rw([ord('r'), 4]) # Get number of writes
            
            self.rw([ord('w'), 0, 1]) # Enable
            assert self.rw([ord('r'), 6])[1][0] == 0x01 # number of reads
            
            self.rw([ord('w'), 0, 0]) # Disable
            
            # Get response
            if self.rw([ord('r'), 7])[1][0] == 0: # ACK
                print("Found device at address {}", a)
            self.rw([ord('r'), 5]) # data
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "Serial tests")
    
    parser.add_argument("port", help = "COMPORT")
    parser.add_argument("--address", "-a", type = int, default = 0b0111011, help = "I2C address")

    args = parser.parse_args()

    m = Monitor(port = args.port)
    
    m.i2c_scan(args.address)
    
    # Interactive
    #while True:
    #    m.prompt()