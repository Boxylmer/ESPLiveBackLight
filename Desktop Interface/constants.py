from enum import Enum
import mss
import mss.tools
import mss.windows
mss.windows.CAPTUREBLT = 0
sct = mss.mss()


SOFTKILL_MODEL = False

class PATH_ORDERS(Enum):
    ALL = 1
    EDGE = 2
    CUSTOM = 3

WINDOW_BORDER_FRACTION = 0.07
REFRESH_TIME_MS = 75
GUI_POLLING_TIME_MS = 100

MICROCHIP_START_BYTE = 55 # U
MICROCHIP_STOP_BYTE = 10  # /n