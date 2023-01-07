
# import serial
from serial import Serial
import serial.tools.list_ports
import numpy as np
import time
import random 

plist = [x.device for x in list(serial.tools.list_ports.comports())]
print(plist)

ser = Serial(plist[0], 200000, timeout=0.0, parity=serial.PARITY_NONE)
# ser.write(b'1')


val1 = 255
val2 = 255
val3 = 255
for _ in range(1000):
    ba = bytearray([1])
    for _ in range(10):
        ba.append(val1); ba.append(val2); ba.append(val3)
    # ba.append(0)
    ser.write(ba)
    val1 = random.randint(0, 155)
    val2 = random.randint(0, 155)
    val3 = random.randint(0, 155)
    print(val1, val2, val3)
    print(ba)
    time.sleep(0.1)


# ser.write(bytearray([1, 100, 0, 100, 100, 100, 100, 100, 0, 100, 100, 100, 100, 100, 0, 100, 100, 100, 100, 0]))

# ser.write(bytearray([1, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 0]))
# def serial_ports():
#     """ Lists serial port names

#         :raises EnvironmentError:
#             On unsupported or unknown platforms
#         :returns:
#             A list of the serial ports available on the system
#     """
#     if sys.platform.startswith('win'):
#         ports = ['COM%s' % (i + 1) for i in range(256)]
#     elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
#         ports = glob.glob('/dev/tty[A-Za-z]*')
#     elif sys.platform.startswith('darwin'):
#         ports = glob.glob('/dev/tty.*')
#     else:
#         raise EnvironmentError('Unsupported platform')
#     result = []
#     for port in ports:
#         try:
#             s = serial.Serial(port)
#             print(port)
#             s.close()
#             print(port)
#             result.append(port)
#         except:
#             pass
#     return result

# serial_ports()