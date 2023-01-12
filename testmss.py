from PIL import Image
import time
import threading
import mss
import mss.tools
import mss.windows
mss.windows.CAPTUREBLT = 0
sct = mss.mss()

def get_master_screenshot():
    """Get a screenshot of the overall virtual screen."""
    complete_screengrab = sct.grab(sct.monitors[0])
    complete_screenshot = Image.frombytes("RGB", complete_screengrab.size, complete_screengrab.bgra, "raw", "BGRX")
    return complete_screenshot

def get_master_screenshot_buffer():
    """Get a screenshot of the overall virtual screen, but improve things slightly by not allocating."""
    complete_screengrab = sct.grab(sct.monitors[0])
    complete_screenshot = Image.frombuffer("RGB", complete_screengrab.size, complete_screengrab.bgra, "raw", "BGRX")
    return complete_screenshot
    
def time_for_all_screenshots_1():
    times = []
    for _ in range(50):
        starttime = time.time()
        get_master_screenshot()
        t = time.time() - starttime
        times.append(t)
    return sum(times) / len(times)
    

# get_master_screenshot().show()

def get_individual_screenshot(monitor_id):
    complete_screengrab = sct.grab(sct.monitors[monitor_id])
    complete_screenshot = Image.frombytes("RGB", complete_screengrab.size, complete_screengrab.bgra, "raw", "BGRX")
    return complete_screenshot

# used to access only individual borders
LOCAL_TOP = (
    0, 
    0, 
    sct.monitors[1]["width"], 
    50
)
LOCAL_BOTTOM = (
    0, 
    sct.monitors[1]["height"] - 50, 
    sct.monitors[1]["width"], 
    sct.monitors[1]["height"]
)
LOCAL_LEFT = (
    0, 
    0, 
    50, 
    sct.monitors[1]["height"]
)
LOCAL_RIGHT = (
    sct.monitors[1]["width"] - 50, 
    0, 
    sct.monitors[1]["width"], 
    sct.monitors[1]["height"]
)


def get_four_boundary_screensots():
    im1 = sct.grab(LOCAL_TOP)
    im2 = sct.grab(LOCAL_BOTTOM)
    im3 = sct.grab(LOCAL_LEFT)
    im4 = sct.grab(LOCAL_RIGHT)
    scrsht1 = Image.frombuffer("RGB", im1.size, im1.bgra, "raw", "BGRX")
    scrsht2 = Image.frombuffer("RGB", im2.size, im2.bgra, "raw", "BGRX")
    scrsht3 = Image.frombuffer("RGB", im3.size, im3.bgra, "raw", "BGRX")
    scrsht4 = Image.frombuffer("RGB", im4.size, im4.bgra, "raw", "BGRX")
    return scrsht1, scrsht2, scrsht3, scrsht4

def time_for_all_screenshots_2():
    times = []
    for _ in range(50):
        starttime = time.time()
        get_individual_screenshot(1)
        get_individual_screenshot(2)
        get_individual_screenshot(3)
        get_individual_screenshot(4)
        t = time.time() - starttime
        times.append(t)
    return sum(times) / len(times)


def time_for_all_screenshots_3():
    times = []
    for _ in range(50):
        starttime = time.time()
        get_master_screenshot_buffer()
        t = time.time() - starttime
        times.append(t)
    return sum(times) / len(times)

def time_for_all_screenshots_4():
    times = []
    for _ in range(50):
        starttime = time.time()
        get_four_boundary_screensots()
        get_four_boundary_screensots()
        get_four_boundary_screensots()
        get_four_boundary_screensots()
        t = time.time() - starttime
        times.append(t)
    return sum(times) / len(times)


class ScreenshotAcquirer:
    def __init__(self, monitor_id) -> None:
        self.screenshot = None
        self.monitor_id = monitor_id

    def get_screenshot(self):
        self.screenshot = get_individual_screenshot(self.monitor_id)
    
    def start(self):
        threading.Thread(target=self.get_screenshot).start()
        return self

    def iscomplete(self): 
        if self.screenshot == None: return False
        else: return True

# what if it's threaded?
def time_for_all_screenshots_5():
    times = []
    for _ in range(50):
        starttime = time.time()
        sa1 = ScreenshotAcquirer(1).start()
        sa2 = ScreenshotAcquirer(2).start()
        sa3 = ScreenshotAcquirer(3).start()
        sa4 = ScreenshotAcquirer(4).start()
        while not(sa1.iscomplete() and sa2.iscomplete() and sa3.iscomplete() and sa4.iscomplete()):
            pass

        t = time.time() - starttime
        times.append(t)
    return sum(times) / len(times)

# print("time for method 1: ", time_for_all_screenshots_1())
# print("time for method 2: ", time_for_all_screenshots_2())
# print("time for method 3: ", time_for_all_screenshots_3())
# print("time for method 4: ", time_for_all_screenshots_4())
print("time for method 4: ", time_for_all_screenshots_5())
