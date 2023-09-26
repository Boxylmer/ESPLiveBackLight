from serial import Serial
import serial.tools.list_ports

class SerialConnection:

    MAX_ATTEMPTS_BEFORE_RECONNECT = 15

    def __init__(self) -> None:
        self.port = None
        self.connection = None
        self.attempt_counter = 0

    def connect(self, port):
        print("Connecting to ", port)
        ports = self.find_serial_ports()
        if port is None: 
            print("Port was not provided")
            return

        self.port = port 

        if self.connection != None:
            if self.isconnected(): self.disconnect()
        
        if port in ports:
            try:
                self.connection = Serial(port, 115200, timeout=0.0, parity=serial.PARITY_NONE)
            except:
                self.connection = None
                print("Connecting to serial failed.")
        else: print("Port doesn't exist.")

    def disconnect(self):
        try:
            self.connection.close()
        except:
            print("Could not close serial port.")
        self.serial = None
    
    def write(self, data):

        if self.connection != None and self.isconnected():
            try: 
                self.connection.write(data)
                self.attempt_counter = 0
            except: 
                print("Warning: Could not write to serial buffer.")
                self.attempt_counter += 1
            if self.attempt_counter > SerialConnection.MAX_ATTEMPTS_BEFORE_RECONNECT:
                self.disconnect()

    def isconnected(self):
        if self.connection == None: return False

        if self.connection.isOpen():
            return True
        else:
            return False

    def keepalive(self):
        if self.port != None and not self.isconnected():
            self.connect(self.port)


    @staticmethod
    def find_serial_ports():
        return [x.device for x in list(serial.tools.list_ports.comports())]
