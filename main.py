# known working on python version 3.8.0


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

# monitor = sct.monitors[1]
# scr_top = sct.grab((monitor["left"], monitor["top"], monitor["left"] + monitor["width"], monitor["top"] + monitor["height"]))
# img = Image.frombytes("RGB", scr_top.size, scr_top.bgra, "raw", "BGRX")
# img.show()


WINDOW_BORDER_FRACTION = 0.01
REFRESH_TIME_MS = 200
GUI_POLLING_TIME_MS = 50

def find_monitor_ids():
    return [*range(1, len(sct.monitors))]
    # return [0]

def top_left_corner(id):
    return sct.monitors[id]["left"], sct.monitors[id]["top"]
def bottom_left_corner(id):
    return sct.monitors[id]["left"], sct.monitors[id]["top"] + sct.monitors[id]["height"]
def top_right_corner(id):
    return sct.monitors[id]["left"] + sct.monitors[id]["width"], sct.monitors[id]["top"]
def bottom_right_corner(id):
    return sct.monitors[id]["left"] + sct.monitors[id]["width"], sct.monitors[id]["top"] + sct.monitors[id]["height"]

class MonitorOrchestrator:
    PX_TOLERANCE = 100 # n-pixels for monitor borders to be considered touching
    MONITOR_LIMIT = 50


    def __init__(self, monitor_borders):
        self.monitor_borders = monitor_borders
        self.monitor_ids = [b.monitor_id for b in monitor_borders]

        self.first_monitor_id = self.monitor_ids[self._first_monitor_idx()]
        self.monitor_id_to_grid_position = self._find_monitor_grid_positions()
        self.grid_position_to_monitor_id = {value: key for key, value in self.monitor_id_to_grid_position.items()} # this only works for dicts with guaranteed unique values

        self.border_monitor_path, self.border_edge_path = self._generate_monitor_side_path(self.first_monitor_id, first_edge='d')
        print(self.border_monitor_path, self.border_edge_path)

    def _top_left_corner(self, border):
        return top_left_corner(border.monitor_id)

    def _bottom_left_corner(self, border):
        return bottom_left_corner(border.monitor_id)

    def _top_right_corner(self, border):
        return top_right_corner(border.monitor_id)

    def _bottom_right_corner(self, border):
        return bottom_right_corner(border.monitor_id)

    def _dist(self, pt1, pt2):
        return ((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)**0.5

    # todo this may be arbitrary
    def _first_monitor_idx(self):
        target = bottom_left_corner(0)  # farthest bottom left of the virtual monitor
        best_distance = self._dist(target, top_right_corner(0))  # naieve initial target that, by definition, must be higher than any corner

        best_candidate_idx = 0
        for idx, monitor_border in enumerate(self.monitor_borders):
            candidate_distance = self._dist(target, self._bottom_left_corner(monitor_border))
            if candidate_distance < best_distance:
                best_candidate_idx = idx
                best_distance = candidate_distance
        # print(best_candidate_idx)
        return best_candidate_idx

    def _find_monitor_grid_positions(self):
        naive_first_position_idx = self._first_monitor_idx()
        naive_first_id = self.monitor_borders[naive_first_position_idx].monitor_id
        naive_first_position = (0, 0)
        remaining_position_ids = self.monitor_ids.copy()
        remaining_position_ids.remove(naive_first_id)
        naive_ids_to_position = {naive_first_id: naive_first_position}

        dirs = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        print("all positions:")
        for pid in self.monitor_ids:
            print("   ", pid, ": ", top_left_corner(pid))
        while len(remaining_position_ids) > 0:
            found_one_during_loop = False  # sets to true if a monitor was in a non-grid position
            for pid in remaining_position_ids:
                # print("Looking for location of monitor: ", pid)
                if found_one_during_loop: break
                for d in dirs:
                    # print("-Looking in direction: ", d)
                    if found_one_during_loop: break
                    original_position = top_left_corner(pid)
                    possible_known_position = original_position[0] - d[0] * sct.monitors[pid]["width"], original_position[1] - d[1] * sct.monitors[pid]["height"]

                    for pid_known in naive_ids_to_position.copy().keys():
                        # print("--currently known positions: ", naive_ids_to_position)
                        # print("--possibly known position: ", possible_known_position)
                        if found_one_during_loop: break
                        known_position = top_left_corner(pid_known)
                        # print("--comparing to known position: ", known_position)
                        if self._dist(possible_known_position, known_position) < MonitorOrchestrator.PX_TOLERANCE:
                            location = naive_ids_to_position[pid_known][0] + d[0], naive_ids_to_position[pid_known][1] + d[1]
                            naive_ids_to_position[pid] = location
                            # print("---FOUND POSITION: monitor ", pid, " at location ", location)
                            remaining_position_ids.remove(pid)
                            found_one_during_loop = True
                            # raise(Exception("---"))
            if not found_one_during_loop:
                raise(Exception("One of the montiors was out of tolerance to be fit into a cardinal grid system!"))


        print("naive: ", naive_ids_to_position)
        # find lowest values and normalize
        lowestx=0
        lowesty=0
        for coordinate in naive_ids_to_position.values():
            if coordinate[0] < lowestx: lowestx = coordinate[0]
            if coordinate[1] < lowesty: lowesty = coordinate[1]

        ids_to_position = {}
        for pid in naive_ids_to_position.keys():
            # shift everything up and flip x and y
            ids_to_position[pid] = naive_ids_to_position[pid][0] - lowestx,(naive_ids_to_position[pid][1] - lowesty) 
        print(ids_to_position)
        # raise(Exception("---"))
        return ids_to_position

    def _rotate_edge_symbol(self, edge_position, direction='clockwise'):
        if direction == 'clockwise':
            if edge_position == 'd': return 'l'
            elif edge_position == 'l': return 'u'
            elif edge_position == 'u': return 'r'
            elif edge_position == 'r': return 'd'
            else: raise Exception("Invalid edge face symbol!")
        elif direction == 'counterclockwise':
            if edge_position == 'd': return 'r'
            elif edge_position == 'r': return 'u'
            elif edge_position == 'u': return 'l'
            elif edge_position == 'l': return 'd'
            else: raise Exception("Invalid edge face symbol!")
        else: raise Exception("Invalid direction!")

    def _get_position_in_direction(self, grid_position, edge_position):
        if edge_position == 'd':
            return (grid_position[0] + 0, grid_position[1] + 1)
        elif edge_position == 'l':
            return (grid_position[0] - 1, grid_position[1] + 0)
        elif edge_position == 'u':
                return (grid_position[0] + 0, grid_position[1] - 1)
        elif edge_position == 'r':
                return (grid_position[0] + 1, grid_position[1] + 0)
        else: raise Exception("Invalid edge position!")

    def _has_neighbor_in_direction(self, grid_position, edge_position):
        neighboring_position = self._get_position_in_direction(grid_position, edge_position)
        for possible_neighbor_position in self.monitor_id_to_grid_position.values():
            if neighboring_position == possible_neighbor_position: return True
        return False

    def _traverse_grid_border(self, monitor_id, current_edge_position, direction='clockwise'):
        grid_position = self.monitor_id_to_grid_position[monitor_id]
        if direction == 'clockwise':
            candidate_edge_position = self._rotate_edge_symbol(current_edge_position, direction='clockwise')
            for _ in range(MonitorOrchestrator.MONITOR_LIMIT):
                print(grid_position, candidate_edge_position)
                if self._has_neighbor_in_direction(grid_position, candidate_edge_position):
                    grid_position = self._get_position_in_direction(grid_position, candidate_edge_position)
                    candidate_edge_position = self._rotate_edge_symbol(candidate_edge_position, direction='counterclockwise')
                else:
                    return self.grid_position_to_monitor_id[grid_position], candidate_edge_position
            raise Exception("Pathing failed, is a monitor (exclusively) diagonal in your setup?")
        elif direction == 'counterclockwise':
            raise Exception("the dev is lazy and didn't write this because it didn't end up being necessary")

    def _generate_monitor_side_path(self, first_monitor_id, first_edge='d'):
        monitor_id_path = [first_monitor_id]
        edge_path = [first_edge]
        for _ in range(MonitorOrchestrator.MONITOR_LIMIT * 4):
            next_monitor_path, next_edge_path = self._traverse_grid_border(monitor_id_path[-1], edge_path[-1])
            if (monitor_id_path[0] == next_monitor_path and edge_path[0] == next_edge_path):
                break
            else:
                monitor_id_path.append(next_monitor_path)
                edge_path.append(next_edge_path)
        return monitor_id_path, edge_path


    #getters

    def get_monitor_grid_position_by_id(self, id):
        return self.monitor_id_to_grid_position[id]


class MonitorBorderPixels:
    def __init__(self, pixel_height, pixel_width, monitor_id):
        self.monitor_id = monitor_id
        self.monitor = sct.monitors[monitor_id]
        self.refresh_screen_size()
        self.update_border_size(pixel_height, pixel_width)
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


mbps = []
monitor_ids = find_monitor_ids()
for i, monitor_id in enumerate(monitor_ids):
    mbps.append(MonitorBorderPixels(20, 40, monitor_id))
orchestrator = MonitorOrchestrator(mbps)

#### make tkinter gui
window = tk.Tk()
window.title("Boxman Fiddlejig")

optionsframe = tk.Frame(window)
edge_mode_var = tk.IntVar()
edge_mode_check = tk.Checkbutton(optionsframe, variable=edge_mode_var, text="Send only to edges", font=('Helvetica 12 bold'))
edge_mode_check.pack(side=tk.LEFT)
optionsframe.pack(expand=False)

def get_edgemode_checkbox():
    if edge_mode_var.get() == 1:
        return True
    else:
        return False

def set_edgemode_checkbox(checked):
    if checked == True:
        edge_mode_var.set(1)
        return
    elif checked == False:
        edge_mode_var.set(0)
        return
    else: raise Exception("Invalid input!")


canvases = []  # we might not need to save these just yet

grids = []
monitor_active_buttons = []
widths_input_fields = []
heights_input_fields = []

monitorframe = tk.Frame(window)
for i, monitor_id in enumerate(monitor_ids):
    frame = tk.Frame(monitorframe)
    canvases.append(tk.Canvas(frame))
    canvases[i].pack(expand=True, fill=tk.BOTH)
    grids.append(CanvasGrid(canvases[i], mbps[i]))

    c, r = orchestrator.get_monitor_grid_position_by_id(monitor_id)
    frame.grid(row=r, column=c, sticky=tk.NSEW)
    monitorframe.grid_columnconfigure(c, weight=1)
    monitorframe.grid_rowconfigure(r, weight=1)

monitorframe.pack(expand=True, fill=tk.BOTH)
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
            for mbpv in mbps:
                try:
                    mbpv.update()
                except:
                    print("WARNING: Model loop failed to ping.")
        
        remaining_time = max(0, REFRESH_TIME_MS/1000 - (time.time() - last_refresh_time))
        # print(remaining_time)
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

