# known working on python version 3.8.0

# todo
# pixel row / height input
# com port search and dropdown
# settings file
# go back over the serial protocol on the microchip

# disable certain monitors / make logic skip those monitors
# specify refresh rate


import threading
from PIL import Image
import numpy as np
import pystray
from pystray import MenuItem as item
import tkinter as tk
import time

from serial import Serial
import serial.tools.list_ports

import mss
import mss.tools
import mss.windows
mss.windows.CAPTUREBLT = 0
sct = mss.mss()
SOFTKILL_MODEL = False

# def get_master_screenshot():
#     """Get a screenshot of the overall virtual screen."""
#     complete_screengrab = sct.grab(sct.monitors[0])
#     complete_screenshot = Image.frombytes("RGB", complete_screengrab.size, complete_screengrab.bgra, "raw", "BGRX")
#     return complete_screenshot
# get_master_screenshot()
# get_master_screenshot().show()

# monitor = sct.monitors[1]
# scr_top = sct.grab((monitor["left"], monitor["top"], monitor["left"] + monitor["width"], monitor["top"] + monitor["height"]))
# img = Image.frombytes("RGB", scr_top.size, scr_top.bgra, "raw", "BGRX")
# img.show()

WINDOW_BORDER_FRACTION = 0.01
REFRESH_TIME_MS = 100
GUI_POLLING_TIME_MS = 100

MICROCHIP_START_BYTE = 55 # U
MICROCHIP_STOP_BYTE = 10  # /n


def remove_info_tokens(arr):
    """Remove all tokens from the bytearray that would otherwise have signal meaning, such as the sequence terminator token."""
    for i in range(2, len(arr) - 1):
        if arr[i] == MICROCHIP_STOP_BYTE:
            arr[i] = MICROCHIP_STOP_BYTE - 1 # clip to 254 and 0
        # we won't need to deal with the start byte as the server won't be watching for it during reading

def find_monitor_ids():
    return [*range(1, len(sct.monitors))]
    # return [0]

def find_serial_ports():
    return [x.device for x in list(serial.tools.list_ports.comports())]

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
        self.monitor_id_to_border_object = {b.monitor_id: b for b in monitor_borders}

        self.first_monitor_id = self.monitor_ids[self._first_monitor_idx()]
        self.monitor_id_to_grid_position = self._find_monitor_grid_positions()
        self.grid_position_to_monitor_id = {value: key for key, value in self.monitor_id_to_grid_position.items()} # this only works for dicts with guaranteed unique values
        
        self.path_mode = 'all' # or 'border'

        # border info
        self.border_monitor_path, \
        self.border_edge_path, \
        self.id_and_side_to_border_order_dict, \
        self.border_order_to_id_and_side_dict = \
        self._generate_monitor_side_path(self.first_monitor_id, first_edge='d')
        print(self.border_monitor_path, self.border_edge_path, self.id_and_side_to_border_order_dict, self.border_order_to_id_and_side_dict)

        self.complete_monitor_path, \
        self.complete_edge_path, \
        self.id_and_side_to_complete_order_dict, \
        self.complete_order_to_id_and_side_dict = self._generate_monitor_total_path()

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

        id_and_side_to_order_dict = {}
        order_to_id_and_side_dict = {}
        assert len(monitor_id_path) ==  len(edge_path)
        for idx, _ in enumerate(monitor_id_path):
            id_and_side = (monitor_id_path[idx], edge_path[idx])
            id_and_side_to_order_dict[id_and_side] = idx
            order_to_id_and_side_dict[idx] = id_and_side
        return monitor_id_path, edge_path, id_and_side_to_order_dict, order_to_id_and_side_dict

    def _generate_monitor_total_path(self):
        complete_monitor_path = []
        for id in monitor_ids:
            complete_monitor_path.append(id)
            complete_monitor_path.append(id)
            complete_monitor_path.append(id)
            complete_monitor_path.append(id)

        complete_edge_path = ('d', 'l', 'u', 'r') * len(self.monitor_ids)
        print
        id_and_side_to_complete_order_dict = {}
        complete_order_to_id_and_side_dict = {}
        assert len(complete_monitor_path) ==  len(complete_edge_path)
        for idx, _ in enumerate(complete_monitor_path):
            id_and_side = (complete_monitor_path[idx], complete_edge_path[idx])
            id_and_side_to_complete_order_dict[id_and_side] = idx
            complete_order_to_id_and_side_dict[idx] = id_and_side

        return complete_monitor_path, complete_edge_path, id_and_side_to_complete_order_dict, complete_order_to_id_and_side_dict

    #setters and commands

    def set_path_mode(self, mode): 
        self.path_mode = mode

    #getters

    def get_monitor_grid_position_by_id(self, id):
        return self.monitor_id_to_grid_position[id]

    def get_order_of_edge(self, monitor_id, side):
        if self.path_mode == 'border':
            key = (monitor_id, side)
            if key in self.id_and_side_to_border_order_dict:
                return self.id_and_side_to_border_order_dict[key]
            else:
                return None
        elif self.path_mode == 'all':
            key = (monitor_id, side)
            if key in self.id_and_side_to_complete_order_dict:
                return self.id_and_side_to_complete_order_dict[key]
            else:
                return None
        else:
            raise Exception("Invalid mode")

    def get_id_and_edge_from_order(self, order):
        if self.path_mode == 'border':
            return self.border_order_to_id_and_side_dict[order]
        elif self.path_mode == 'all':
            return self.complete_order_to_id_and_side_dict[order]
        else:
            raise Exception("Invalid mode")

    def get_num_edges(self): 
        if self.path_mode == 'border':
            return len(self.border_order_to_id_and_side_dict)
        elif self.path_mode == 'all':
            return len(self.monitor_ids) * 4

    def get_pixel_row(self, id, edge):
        if edge == 'u':
            return self.monitor_id_to_border_object[id].get_top()
        elif edge == 'd':
            return self.monitor_id_to_border_object[id].get_bottom()
        elif edge == 'l':
            return self.monitor_id_to_border_object[id].get_left()
        elif edge == 'r':
            return self.monitor_id_to_border_object[id].get_right()

    def get_pixel_stream(self):
        data = bytearray([MICROCHIP_START_BYTE])
        
        if self.path_mode == 'border':
            id_and_side_lookup = self.border_order_to_id_and_side_dict
        elif self.path_mode == 'all':
            id_and_side_lookup = self.complete_order_to_id_and_side_dict
        else: raise Exception("Path mode was not valid")
        
        for i in range(self.get_num_edges()):
            pid, side = id_and_side_lookup[i]
            row = self.get_pixel_row(pid, side)
            if side == 'u':
                rgbrow = row
            elif side == 'd':
                rgbrow = np.flip(row)
            elif side == 'l':
                rgbrow = np.flip(row)
            elif side == 'r':
                rgbrow = row
            
            for colorval in rgbrow:
                data.append(round(colorval[2]))
                data.append(round(colorval[1]))
                data.append(round(colorval[0]))
        remove_info_tokens(data)
        data.append(MICROCHIP_STOP_BYTE)
        return data

class MonitorBorderPixels:
    def __init__(self, pixel_height, pixel_width, monitor_id):
        self.monitor_id = monitor_id
        self.monitor = sct.monitors[monitor_id]
        
        self.monitor_bbox = (  # todo possibly remove
            self.monitor["left"], 
            self.monitor["top"], 
            self.monitor["left"] + self.monitor["width"], 
            self.monitor["top"] + self.monitor["height"]
        )

        self.refresh_screen_size()
        self.update_border_size(pixel_height, pixel_width)
        self.update_img()
        self.update()
        self.kill_thread = False
        self.subthread = threading.Thread(target=self.screencapture_subprocess).start()

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
        st = time.time()
        self.img = Image.frombuffer("RGB", scr.size, scr.bgra, "raw", "BGRX")
        print("Image conversion time monitor ", self.monitor_id, ": ", time.time() - st)
    
    def screencapture_subprocess(self):
        last_refresh_time = time.time()
        while True:
            if self.kill_thread: return
            if (time.time() - last_refresh_time) * 1000 > REFRESH_TIME_MS:
                last_refresh_time = time.time()
                self.update_img()
                print("Total frame time for monitor ", self.monitor_id, ": ", time.time() - last_refresh_time)
            else:
                remaining_time = max(0, REFRESH_TIME_MS/1000 - (time.time() - last_refresh_time))
                time.sleep(remaining_time)

    def terminate_subprocess(self):
        self.kill_thread = True

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
        start = time.time()
        self.pix_left = np.asarray(self.img.crop(self.LOCAL_LEFT).resize((1, self.pixel_height))).squeeze()

        self.pix_right = np.asarray(self.img.crop(self.LOCAL_RIGHT).resize((1, self.pixel_height))).squeeze()
        self.pix_top = np.asarray(self.img.crop(self.LOCAL_TOP).resize((self.pixel_width, 1))).squeeze()
        self.pix_bottom = np.asarray(self.img.crop(self.LOCAL_BOTTOM).resize((self.pixel_width, 1))).squeeze()
        print("image update time: ", time.time() - start)
    def get_top(self): return self.pix_top
    def get_bottom(self): return self.pix_bottom
    def get_left(self): return self.pix_left
    def get_right(self): return self.pix_right


#### define drawing things
class CanvasGrid:
    def __init__(self, canvas, mbpv, orchestrator):
        self.DEFAULT_COLOR = "#%02x%02x%02x" % (50, 50, 50)
        self.canvas = canvas
        self.mbpv = mbpv
        self.orchestrator = orchestrator
        self.initialize_objects()

    def initialize_objects(self):
        self.canvas.delete("all")
        self.top_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_width)]
        self.bottom_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_width)]
        self.left_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_height)]
        self.right_pixel_ids = [self.canvas.create_rectangle(1, 1, 1, 1, fill=self.DEFAULT_COLOR) for _ in range(self.mbpv.pixel_height)]

        self.monitor_text = self.canvas.create_text(1, 1, text="Monitor " + str(self.mbpv.monitor_id), fill="black", font=('Helvetica 15 bold'), anchor="center")

        self.top_text = self.canvas.create_text(1, 1, text="top", fill="black", font=('Helvetica 15 bold'), anchor=tk.N)
        self.bottom_text = self.canvas.create_text(1, 1, text="bot", fill="black", font=('Helvetica 15 bold'), anchor=tk.S)
        self.left_text = self.canvas.create_text(1, 1, text=" 123456789abc↑defg", fill="black", font=('Helvetica 15 bold'), anchor=tk.W)
        self.right_text = self.canvas.create_text(1, 1, text="123456789abcdefg↑ ", fill="black", font=('Helvetica 15 bold'), anchor=tk.E)
       
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

    def _get_side_text(self, side):
        result = self.orchestrator.get_order_of_edge(self.mbpv.monitor_id, side)
        if result == None: result = "-"
        elif result == 0: result = "start here!"
        else: result = str(result)
        
        if side == 'l': result = ' ' + result
        elif side == 'r': result = result + ' '
        
        return result 


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

        self.canvas.coords(self.top_text, self.canvas.winfo_width()/2, self._pixel_coords(0, "LEFT")[1])
        self.canvas.coords(self.bottom_text, self.canvas.winfo_width()/2, self._pixel_coords(0, "BOTTOM")[1])
        self.canvas.coords(self.left_text, self._pixel_coords(0, "TOP")[3], self.canvas.winfo_height()/2)
        self.canvas.coords(self.right_text, self._pixel_coords(0, "RIGHT")[0], self.canvas.winfo_height()/2)

        
        self.canvas.itemconfigure(self.top_text, text=self._get_side_text('u'))
        self.canvas.itemconfigure(self.bottom_text, text=self._get_side_text('d'))
        self.canvas.itemconfigure(self.left_text, text=self._get_side_text('l'))
        self.canvas.itemconfigure(self.right_text, text=self._get_side_text('r'))

       
            
mbps = []
monitor_ids = find_monitor_ids()
for i, monitor_id in enumerate(monitor_ids):
    mbps.append(MonitorBorderPixels(5, 14, monitor_id))
orchestrator = MonitorOrchestrator(mbps)

#### make tkinter gui
window = tk.Tk()
window.title("Boxman Fiddlejig")

optionsframe = tk.Frame(window)
optionsframe.pack(expand=False)

### TK variables to be used globally 
edge_mode_var = tk.IntVar()
def toggle_orchestrator_mode():
    if edge_mode_var.get() == 1:
        orchestrator.set_path_mode('border')
    else:
        orchestrator.set_path_mode('all')

def set_edgemode_checkbox(checked):
    if checked == True:
        edge_mode_var.set(1)
        return
    elif checked == False:
        edge_mode_var.set(0)
        return
    else: raise Exception("Invalid input!")

# edge mode checkbutton
edge_mode_check = tk.Checkbutton(optionsframe, variable=edge_mode_var, command=toggle_orchestrator_mode, text="Send only to edges", font=('Helvetica 12 bold'))
edge_mode_check.pack(side=tk.LEFT)


# pixel width and height entry form
pixelframe = tk.Frame(optionsframe)
def validate_and_handle_pixelwidthentry(entry, action_type) -> bool:
    result = enter_only_max_two_digits(entry, action_type)
    if result:
        print("Pixel width: ", entry)
        pass # todo, something with the end
    return result
def validate_and_handle_pixelheightentry(entry, action_type) -> bool:
    result = enter_only_max_two_digits(entry, action_type)
    if result:
        print("Pixel width: ", entry)
        pass # todo, something with the end
    return result
def enter_only_max_two_digits(entry, action_type) -> bool:
    if action_type == '1' and not entry.isdigit():
        return False
    if action_type == '1' and float(entry) > 100:
        return False
    return True
v_pixelwidthentry = (window.register(validate_and_handle_pixelwidthentry), '%P', '%d')
v_pixelheightentry = (window.register(validate_and_handle_pixelheightentry), '%P', '%d')

pixelwidthlabel = tk.Label(pixelframe, text="Pixel Width", font=('Helvetica 12 bold'))
pixelwidthlabel.grid(row=0, column=0)
pixelwidthentry = tk.Entry(pixelframe, validate='key', validatecommand=v_pixelwidthentry)
pixelwidthentry.grid(row=0, column=1)
pixelheightlabel = tk.Label(pixelframe, text="Pixel Height", font=('Helvetica 12 bold'))
pixelheightlabel.grid(row=1, column=0)
pixelheightentry = tk.Entry(pixelframe, validate='key', validatecommand=v_pixelheightentry)
pixelheightentry.grid(row=1, column=1)
pixelframe.pack(side=tk.LEFT)

portframe = tk.Frame(optionsframe)
com_port_options = find_serial_ports()
com_port_selection = tk.StringVar()
com_port_selection.set("-")
com_port_dropdown = tk.OptionMenu(portframe, com_port_selection, *com_port_options)
com_port_dropdown.pack(side=tk.BOTTOM)
# com_port_options_label = tk.Label(portframe, text="PORT", font=('Helvetica 12 bold'))
# com_port_options_label.pack(side=tk.TOP)
def update_com_port_dropdown():
    # com_port_selection.set('')
    com_port_dropdown['menu'].delete(0, 'end')
    new_choices = find_serial_ports()
    for choice in new_choices:
        com_port_dropdown['menu'].add_command(label=choice, command=tk._setit(com_port_selection, choice))

com_port_refresh_btn = tk.Button(portframe, text="Refresh Ports", font=('Helvetica 8 bold'), command=update_com_port_dropdown)
com_port_refresh_btn.pack(side=tk.TOP)
portframe.pack(side=tk.LEFT)

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
    grids.append(CanvasGrid(canvases[i], mbps[i], orchestrator))

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
    for mbp in mbps: mbp.terminate_subprocess()
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

window.protocol('WM_DELETE_WINDOW', hide_window)   

plist = [x.device for x in list(serial.tools.list_ports.comports())]
print(plist)
ser = Serial(plist[0], 115200, timeout=0.0, parity=serial.PARITY_NONE)

def ping_model():
    global SOFTKILL_MODEL
    last_refresh_time = time.time()
    while True:
        start_time = time.time()
        if SOFTKILL_MODEL:
            SOFTKILL_MODEL = False
            return
        if (time.time() - last_refresh_time) * 1000 > REFRESH_TIME_MS:
            last_refresh_time = time.time()
            try:
                for mbpv in mbps:
                    mbpv.update() 
            except:
                print("WARNING: Model loop failed to ping.")
            stream = orchestrator.get_pixel_stream()
            
            ser.write(stream)
        # print("Total frame time: ", time.time() - start_time)
        remaining_time = max(0, REFRESH_TIME_MS/1000 - (time.time() - last_refresh_time))
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

    time.sleep(remaining_time)
