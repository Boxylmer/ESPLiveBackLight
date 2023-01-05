import threading
from PIL import Image
import numpy as np
import pystray
from pystray import MenuItem as item
import tkinter as tk
import time

import mss
import mss.tools
sct = mss.mss()

WINDOW_BORDER_FRACTION = 0.05
REFRESH_TIME_MS = 200
GUI_POLLING_TIME_MS = 20

def find_monitor_ids():
    return [*range(1, len(sct.monitors))]

class MonitorBorderPixValues:
    def __init__(self, pixel_height, pixel_width, monitor_id):
        self.monitor_id = monitor_id
        self.monitor = sct.monitors[monitor_id]
        self.refresh_screen_size()
        self.update_border_size(pixel_height, pixel_width)
        self.update()

    def refresh_screen_size(self):

        w_margin = round(WINDOW_BORDER_FRACTION * self.monitor["width"])
        h_margin = round(WINDOW_BORDER_FRACTION * self.monitor["height"])

        self.TOP = (self.monitor["left"], self.monitor["top"], self.monitor["width"], self.monitor["top"] + h_margin)
        self.BOTTOM = (self.monitor["left"], self.monitor["height"]-h_margin, self.monitor["width"], self.monitor["height"])
        self.LEFT = (self.monitor["left"], self.monitor["top"], self.monitor["left"]+w_margin, self.monitor["height"])
        self.RIGHT = (self.monitor["width"]-w_margin, self.monitor["top"], self.monitor["width"], self.monitor["height"])


    def update_border_size(self, pixel_height, pixel_width):
        self.pixel_height = pixel_height
        self.pixel_width = pixel_width

    def get_color(self, n, location):
        if location == "TOP":
            c = self.pix_top[n]
        elif location == "BOTTOM":
            c = self.pix_bottom[n]
        elif location == "LEFT":
            c = self.pix_left[n]
        elif location == "RIGHT":
            c = self.pix_right[n]
        return "#%02x%02x%02x" % (c[0], c[1], c[2])

    def update(self):
        scr_top = sct.grab(self.TOP)
        scr_bottom = sct.grab(self.BOTTOM)
        scr_left = sct.grab(self.LEFT)
        scr_right = sct.grab(self.RIGHT)

        img_left = Image.frombytes("RGB", scr_left.size, scr_left.bgra, "raw", "BGRX")
        img_right = Image.frombytes("RGB", scr_right.size, scr_right.bgra, "raw", "BGRX")
        img_top = Image.frombytes("RGB", scr_top.size, scr_top.bgra, "raw", "BGRX")
        img_bottom = Image.frombytes("RGB", scr_bottom.size, scr_bottom.bgra, "raw", "BGRX")


        self.pix_left = np.array(img_left.resize((1, self.pixel_height))).squeeze()
        self.pix_right = np.array(img_right.resize((1, self.pixel_height))).squeeze()
        self.pix_top = np.array(img_top.resize((self.pixel_width, 1))).squeeze()
        self.pix_bottom = np.array(img_bottom.resize((self.pixel_width, 1))).squeeze()

#### define drawing things
class CanvasGrid:
    def __init__(self, canvas, mbpv):
        self.DEFAULT_COLOR = "#%02x%02x%02x" % (50, 50, 50)
        self.canvas = canvas
        self.mbpv = mbpv
        self.initialize_objects()

    def initialize_objects(self):
        self.canvas.delete("all")
        self.top_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_width)]
        self.bottom_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_width)]
        self.left_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_height)]
        self.right_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_height)]

        self.monitor_text = self.canvas.create_text(1, 1, text="Monitor " + str(self.mbpv.monitor_id), fill="black", font=('Helvetica 15 bold'), anchor="center")
       
    def _pixel_coords(self, n, location):
        n_y = self.mbpv.pixel_height + 2
        n_x = self.mbpv.pixel_width + 2
        h = self.canvas.winfo_height()
        w = self.canvas.winfo_width()

        if location == "TOP":
            return ((n+1)/n_x * w, 0, (n+2)/n_x * w, 1/n_y * h)
        elif location == "BOTTOM":
            return ((n+1)/n_x * w, (n_y-1)/n_y * h, (n+2)/n_x * w, h)
        elif location == "LEFT":
            return (0, (n+1)/n_y * h, 1/n_x * w, (n+2)/n_y * h)
        elif location == "RIGHT":
            return ((n_x-1)/n_x * w, (n+1)/n_y * h, w, (n+2)/n_y * h)

    def update(self):
        for i, pid in enumerate(self.top_pixel_ids):
            self.canvas.coords(pid, self._pixel_coords(i, "TOP"))
            self.canvas.itemconfig(pid, fill=self.mbpv.get_color(i, "TOP"))

        for i, pid in enumerate(self.bottom_pixel_ids):
            self.canvas.coords(pid, self._pixel_coords(i, "BOTTOM"))
            self.canvas.itemconfig(pid, fill=self.mbpv.get_color(i, "BOTTOM"))
        
        for i, pid in enumerate(self.left_pixel_ids):
            self.canvas.coords(pid, self._pixel_coords(i, "LEFT"))
            self.canvas.itemconfig(pid, fill=self.mbpv.get_color(i, "LEFT"))

        for i, pid in enumerate(self.right_pixel_ids):
            self.canvas.coords(pid, self._pixel_coords(i, "RIGHT"))
            self.canvas.itemconfig(pid, fill=self.mbpv.get_color(i, "RIGHT"))

        self.canvas.coords(self.monitor_text, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)


#### make tkinter gui
window = tk.Tk()
window.title("Boxman Fiddlejig")
ipframe = tk.Frame(window)
ipentry = tk.Entry(ipframe)
ipentry.grid(row=0, column=1)
urllabel = tk.Label(ipframe, text="Device URL:")
urllabel.grid(row=0, column=0)
ipframe.pack()
canvases = []  # we might not need to save these just yet
mbpvs = []
grids = []
monitor_active_buttons = []
widths_input_fields = []
heights_input_fields = []

for monitor_id in find_monitor_ids():
    frame = tk.Frame(window)
    sframe = tk.Frame(frame)
    mframe = tk.Frame(frame)
    sframe.pack()
    mframe.pack(fill="both", expand=True)

    t = tk.Label(sframe,text="Active", font=('Helvetica 12 bold'))
    t.grid(row=0, column=0, columnspan=3)
    monitor_active_buttons.append(tk.Checkbutton(sframe))
    monitor_active_buttons[-1].grid(row=0, column=4)

    canvases.append(tk.Canvas(mframe))
    canvases[-1].pack(fill="both", expand=True)
    mbpvs.append(MonitorBorderPixValues(20, 40, 1))
    
    grids.append(CanvasGrid(canvases[-1], mbpvs[-1]))

    frame.pack(fill="both", expand=True, anchor=tk.S)
    

# load the save file and set default values


# Set the size of the window
window.geometry("700x350")


# Define a function for quit the window
def quit_window(icon, item):
    global SOFTKILL_MODEL
    SOFTKILL_MODEL = True
    icon.stop()
    window.destroy()

# Define a function to show the window again
def show_window(icon, item):
   icon.stop()
   window.after(0,window.deiconify())

# Hide the window and show on the system taskbar
def hide_window():
   window.withdraw()
   image=Image.open("think.ico")
   menu=(
    item('Quit', quit_window), 
    item('Show', show_window, default=True),)
   icon=pystray.Icon("name", image, "My System Tray Icon", menu)
   icon.run()

window.protocol('WM_DELETE_WINDOW', hide_window)   # uncomment to reactivate tray behavior

SOFTKILL_MODEL = False
def ping_model():
    global SOFTKILL_MODEL
    last_refresh_time = time.time()
    while True:
        if SOFTKILL_MODEL:
            SOFTKILL_MODEL = False
            return
        if (time.time() - last_refresh_time) * 1000 > REFRESH_TIME_MS:
            last_refresh_time = time.time()
            for mbpv in mbpvs:
                try:
                    mbpv.update()
                except:
                    print("WARNING: Model loop failed to ping.")
        
        remaining_time = max(0, REFRESH_TIME_MS/1000 - (time.time() - last_refresh_time))
        print(remaining_time)
        time.sleep(remaining_time)

threading.Thread(target=ping_model).start()

last_refresh_time = time.time()
while True:
    if (time.time() - last_refresh_time) * 1000 > GUI_POLLING_TIME_MS:
        last_refresh_time = time.time()
        for grid in grids:
            grid.update()

    window.update_idletasks()
    window.update()
    remaining_time = max(0, GUI_POLLING_TIME_MS/1000 - (time.time() - last_refresh_time))
    # print(GUI_POLLING_TIME_MS/1000 - (time.time() - last_refresh_time))

    time.sleep(remaining_time)

