# known working on python version 3.8.0

# todo
# specify refresh rate

import threading
import time

from Application import constants
from Application.constants import REFRESH_TIME_MS, GUI_POLLING_TIME_MS
from Application.utils import find_monitor_ids

from Application.Settings import Settings

settings = Settings()

from Application import MonitorOrchestrator, MonitorBorderPixels, SerialConnection, GUI

#### define drawing things
            
mbps = []

for i, monitor_id in enumerate(find_monitor_ids()):
    mbps.append(MonitorBorderPixels(settings.get_pixel_width(), settings.get_pixel_height(), monitor_id))
orchestrator = MonitorOrchestrator(mbps)
orchestrator.set_enabled_monitors(settings.get_enabled_monitor_ids())

ser = SerialConnection()
ser.connect(settings.get_last_com_port())

gui = GUI(orchestrator, settings, ser)



def ping_model():
    last_refresh_time = time.time()
    while not constants.SOFTKILL_MODEL:
        if (time.time() - last_refresh_time) * 1000 > REFRESH_TIME_MS:
            last_refresh_time = time.time()

            ser.keepalive()

            try:
                orchestrator.update()
                stream = orchestrator.get_pixel_stream()
                ser.write(stream)
            except:
                print("WARNING: Model loop failed to ping.")
            
        remaining_time = max(0, REFRESH_TIME_MS/1000 - (time.time() - last_refresh_time))

        time.sleep(remaining_time)

threading.Thread(target=ping_model).start()


def start():
    last_refresh_time = time.time()
    while not constants.SOFTKILL_MODEL:
        if (time.time() - last_refresh_time) * 1000 > GUI_POLLING_TIME_MS:
            last_refresh_time = time.time()
            
            try:
                gui.update_grid()
            except:
                print("Warning, grid couldn't update.")
        gui.update_tk()

        if gui.wire_order_dragndrop.needs_initialization():
            gui.wire_order_dragndrop.initialize_locations()

        remaining_time = max(0, GUI_POLLING_TIME_MS/1000 - (time.time() - last_refresh_time))
        time.sleep(remaining_time)

# start()
if __name__ == "__main__":
    start()

