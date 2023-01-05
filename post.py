
import serial
from serial.tools import list_ports


import serial.tools.list_ports

plist = [x.device for x in list(serial.tools.list_ports.comports())]

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