import time 
import threading
import numpy as np 
from PIL import Image
from .constants import sct, WINDOW_BORDER_FRACTION

class MonitorBorderPixels:
    def __init__(self, pixel_width, pixel_height, monitor_id):
        self.monitor_id = monitor_id
        self.monitor = sct.monitors[monitor_id]
        
        self.monitor_bbox = (  # todo possibly remove
            self.monitor["left"], 
            self.monitor["top"], 
            self.monitor["left"] + self.monitor["width"], 
            self.monitor["top"] + self.monitor["height"]
        )

        self.enabled = True

        self.refresh_screen_size()
        self._update_border_dimensions(pixel_width, pixel_height)
        self.PENDING_UPDATE = False
        self.update_img()

        self.update()

    def refresh_screen_size(self):

        w_margin = round(WINDOW_BORDER_FRACTION * self.monitor["width"])
        h_margin = round(WINDOW_BORDER_FRACTION * self.monitor["height"])

        self.TOP = (
            self.monitor["left"], 
            self.monitor["top"], 
            self.monitor["left"] + self.monitor["width"], 
            self.monitor["top"] + h_margin
        )
        self.BOTTOM = (
            self.monitor["left"], 
            self.monitor["top"] + self.monitor["height"] - h_margin, 
            self.monitor["left"] + self.monitor["width"], 
            self.monitor["top"] + self.monitor["height"]
        )
        self.LEFT = (
            self.monitor["left"], 
            self.monitor["top"], 
            self.monitor["left"] + w_margin, 
            self.monitor["top"] + self.monitor["height"]
        )
        self.RIGHT = (
            self.monitor["left"] + self.monitor["width"] - w_margin, 
            self.monitor["top"], 
            self.monitor["left"] + self.monitor["width"], 
            self.monitor["top"] + self.monitor["height"]
        )

        self.LOCAL_TOP = (
            0, 
            0, 
            self.monitor["width"], 
            h_margin
        )
        self.LOCAL_BOTTOM = (
            0, 
            self.monitor["height"] - h_margin, 
            self.monitor["width"], 
            self.monitor["height"]
        )
        self.LOCAL_LEFT = (
            0, 
            0, 
            w_margin, 
            self.monitor["height"]
        )
        self.LOCAL_RIGHT = (
            self.monitor["width"] - w_margin, 
            0, 
            self.monitor["width"], 
            self.monitor["height"]
        )

    def update_img(self):
        scr = sct.grab(self.monitor)
        self.img = Image.frombuffer("RGB", scr.size, scr.bgra, "raw", "BGRX")
    
    def screencapture_subprocess(self):        
        st = time.time()
        self.update_img()
        self.pix_left = np.asarray(self.img.crop(self.LOCAL_LEFT).resize((1, self.pixel_height))).squeeze()
        self.pix_right = np.asarray(self.img.crop(self.LOCAL_RIGHT).resize((1, self.pixel_height))).squeeze()
        self.pix_top = np.asarray(self.img.crop(self.LOCAL_TOP).resize((self.pixel_width, 1))).squeeze()
        self.pix_bottom = np.asarray(self.img.crop(self.LOCAL_BOTTOM).resize((self.pixel_width, 1))).squeeze()
        self.PENDING_UPDATE = False
        # print("Total screenshot time for monitor ", self.monitor_id, ": ", time.time() - st)

    def _update_border_dimensions(self, pixel_width, pixel_height):
        self.pixel_height = pixel_height
        self.pixel_width = pixel_width

    def get_color(self, n, location):
        if self.enabled:
            if location == "TOP":
                c = self.pix_top[n]
            elif location == "BOTTOM":
                c = self.pix_bottom[n]
            elif location == "LEFT":
                c = self.pix_left[n]
            elif location == "RIGHT":
                c = self.pix_right[n]
            return "#%02x%02x%02x" % (c[0], c[1], c[2])
        else: return "#%02x%02x%02x" % (0, 0, 0)

    def update(self):
        if not self.PENDING_UPDATE and self.enabled:
            self.PENDING_UPDATE = True
            threading.Thread(target=self.screencapture_subprocess).start()
       
    
    def enable(self): self.enabled = True
    def disable(self): self.enabled = False

    def get_top(self): 
        if self.enabled: return self.pix_top
        else: return np.array([])
    def get_bottom(self): 
        if self.enabled: return self.pix_bottom
        else: return np.array([])
    def get_left(self): 
        if self.enabled: return self.pix_left
        else: return np.array([])
    def get_right(self): 
        if self.enabled: return self.pix_right
        else: return np.array([])

