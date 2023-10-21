import time
import numpy as np 

from .constants import sct, PATH_ORDERS, MICROCHIP_START_BYTE, MICROCHIP_STOP_BYTE
from .utils import top_left_corner, bottom_left_corner, top_right_corner, bottom_right_corner
from .utils import find_monitor_ids, remove_info_tokens

class MonitorOrchestrator:
    PX_TOLERANCE = 100 # n-pixels for monitor borders to be considered touching
    MONITOR_LIMIT = 50

    def __init__(self, monitor_borders):
        self.monitor_borders = monitor_borders
        self.monitor_ids = [b.monitor_id for b in monitor_borders]
        print("MID", self.monitor_ids)
        self.monitor_id_to_border_object = {b.monitor_id: b for b in monitor_borders}

        self.first_monitor_id = self.monitor_ids[self._first_monitor_idx()]
        self.monitor_id_to_grid_position = self._find_monitor_grid_positions()
        self.grid_position_to_monitor_id = {value: key for key, value in self.monitor_id_to_grid_position.items()} # this only works for dicts with guaranteed unique values
        
        self.path_mode = PATH_ORDERS.ALL # or 'border' or 'custom'

        # border info
        _, \
        _, \
        self.id_and_side_to_border_order_dict, \
        self.border_order_to_id_and_side_dict = \
        self._generate_monitor_side_path(self.first_monitor_id, first_edge='d')

        self.monitor_id_path, \
        _, \
        self.id_and_side_to_complete_order_dict, \
        self.complete_order_to_id_and_side_dict = self._generate_monitor_total_path()

        print(self.id_and_side_to_complete_order_dict)
        print(self.complete_order_to_id_and_side_dict)
        # examples are for border
        # monitor path                          -> [2, 2, 3, 3, 4, 4, 1, 1]  
        #   i.e., given an index, what monitor is this on?
        # edge path                             -> ['d', 'l', 'l', 'u', 'u', 'r', 'r', 'd']
        #   i.e., given an index, what direction is this on? 
        # id and side to complete order dict    -> {(2, 'd'): 0, (2, 'l'): 1, (3, 'l'): 2, (3, 'u'): 3, (4, 'u'): 4, (4, 'r'): 5, (1, 'r'): 6, (1, 'd'): 7}
        # comnplete order to id and side dict   -> {0: (2, 'd'), 1: (2, 'l'), 2: (3, 'l'), 3: (3, 'u'), 4: (4, 'u'), 5: (4, 'r'), 6: (1, 'r'), 7: (1, 'd')}
        
        self.generate_monitor_custom_path()

        print(self.id_and_side_to_custom_order_dict)
        print(self.custom_order_to_id_and_side_dict)

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
        return best_candidate_idx

    def _find_monitor_grid_positions(self):
        naive_first_position_idx = self._first_monitor_idx()
        naive_first_id = self.monitor_borders[naive_first_position_idx].monitor_id
        naive_first_position = (0, 0)
        remaining_position_ids = self.monitor_ids.copy()
        remaining_position_ids.remove(naive_first_id)
        naive_ids_to_position = {naive_first_id: naive_first_position}

        dirs = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
     
        for pid in self.monitor_ids:
            print("   ", pid, ": ", top_left_corner(pid))
        while len(remaining_position_ids) > 0:
            found_one_during_loop = False  # sets to true if a monitor was in a non-grid position
            for pid in remaining_position_ids:
                if found_one_during_loop: break
                for d in dirs:
                    if found_one_during_loop: break
                    original_position = top_left_corner(pid)
                    possible_known_position = original_position[0] - d[0] * sct.monitors[pid]["width"], original_position[1] - d[1] * sct.monitors[pid]["height"]

                    for pid_known in naive_ids_to_position.copy().keys():
                        if found_one_during_loop: break
                        known_position = top_left_corner(pid_known)
                        if self._dist(possible_known_position, known_position) < MonitorOrchestrator.PX_TOLERANCE:
                            location = naive_ids_to_position[pid_known][0] + d[0], naive_ids_to_position[pid_known][1] + d[1]
                            naive_ids_to_position[pid] = location
                            remaining_position_ids.remove(pid)
                            found_one_during_loop = True
            if not found_one_during_loop:
                raise(Exception("One of the montiors was out of tolerance to be fit into a cardinal grid system!"))

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
                if self._has_neighbor_in_direction(grid_position, candidate_edge_position):
                    grid_position = self._get_position_in_direction(grid_position, candidate_edge_position)
                    candidate_edge_position = self._rotate_edge_symbol(candidate_edge_position, direction='counterclockwise')
                else:
                    return self.grid_position_to_monitor_id[grid_position], candidate_edge_position
            raise Exception("Pathing failed, is a monitor (exclusively) diagonal in your setup?")
        elif direction == 'counterclockwise':
            raise Exception("the dev is lazy and didn't write this because it didn't end up being necessary")

    def _generate_monitor_total_path(self):
        complete_monitor_path = []
        for id in self.monitor_ids:
            complete_monitor_path.append(id)
            complete_monitor_path.append(id)
            complete_monitor_path.append(id)
            complete_monitor_path.append(id)

        complete_edge_path = ('d', 'l', 'u', 'r') * len(self.monitor_ids)
        id_and_side_to_complete_order_dict = {}
        complete_order_to_id_and_side_dict = {}
        assert len(complete_monitor_path) ==  len(complete_edge_path)
        for idx, _ in enumerate(complete_monitor_path):
      
            id_and_side = (complete_monitor_path[idx], complete_edge_path[idx])
            id_and_side_to_complete_order_dict[id_and_side] = idx
            complete_order_to_id_and_side_dict[idx] = id_and_side
        return complete_monitor_path, complete_edge_path, id_and_side_to_complete_order_dict, complete_order_to_id_and_side_dict

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

    def generate_monitor_custom_path(self, order=None, directions=None):
        if order is None:
            self.id_and_side_to_custom_order_dict = self.id_and_side_to_complete_order_dict
            self.custom_order_to_id_and_side_dict = self.complete_order_to_id_and_side_dict
            self.custom_order_edge_directions = [1] * len(self.monitor_id_path)
            return
        
        assert ((order is not None) and (directions is not None))
        
        id_and_side_to_order_dict = {}
        order_to_id_and_side_dict = {}
        idx_to_direction = []
        # order     -> [5, 4, 2, 6, 1, 0, 3]
        # directions-> [1, 1,-1, 1,-1,-1, 1] (corresponds to the default, we need to convert it to the order)
        # default   -> [0, 1, 2, 3, 4, 5, 6]

        for idx, _ in enumerate(self.monitor_id_path):
            mapped_custom_id = order[idx] # -> 5
            id_and_side = (self.complete_order_to_id_and_side_dict[mapped_custom_id]) # -> Something like (2, 'l)
            id_and_side_to_order_dict[id_and_side] = idx  # now 1 -> (2, 'l')
            order_to_id_and_side_dict[idx] = id_and_side  # and (2, 'l') -> 1
            idx_to_direction.append(directions[mapped_custom_id])
    
        self.id_and_side_to_custom_order_dict = id_and_side_to_order_dict
        self.custom_order_to_id_and_side_dict = order_to_id_and_side_dict
        self.custom_order_edge_directions = idx_to_direction 

        print(self.id_and_side_to_custom_order_dict)
        print(self.custom_order_to_id_and_side_dict)
        print(self.custom_order_edge_directions)
        return
    
    #setters and commands

    def update_border_dimensions(self, pixel_width, pixel_height):
        for mbp in self.monitor_borders:
            mbp._update_border_dimensions(pixel_width, pixel_height)

    def set_path_mode(self, mode): 
        self.path_mode = mode

    def set_enabled_monitors(self, enabled_ids):
        for pid in find_monitor_ids(): self.monitor_id_to_border_object[pid].disable()
        for pid in enabled_ids: self.monitor_id_to_border_object[pid].enable()

    def update(self):
        start = time.time()
        for mbp in self.monitor_borders:
            mbp.update()
      

    #getters

    def get_monitor_grid_position_by_id(self, id):
        return self.monitor_id_to_grid_position[id]

    def get_order_of_edge(self, monitor_id, side):
        if self.path_mode == PATH_ORDERS.EDGE:
            key = (monitor_id, side)
            if key in self.id_and_side_to_border_order_dict:
                return self.id_and_side_to_border_order_dict[key]
            else:
                return None
        elif self.path_mode == PATH_ORDERS.ALL:
            key = (monitor_id, side)
            if key in self.id_and_side_to_complete_order_dict:
                return self.id_and_side_to_complete_order_dict[key]
            else:
                return None
        elif self.path_mode == PATH_ORDERS.CUSTOM:
            # untested
            key = (monitor_id, side)
            if key in self.id_and_side_to_complete_order_dict:
                return self.id_and_side_to_complete_order_dict[key]
            else:
                return None
        else:
            raise Exception("Invalid mode")

    def get_id_and_edge_from_order(self, order): # todo remove / comment
        if self.path_mode == PATH_ORDERS.EDGE:
            return self.border_order_to_id_and_side_dict[order]
        elif self.path_mode == PATH_ORDERS.ALL:
            return self.complete_order_to_id_and_side_dict[order]
        elif self.path_mode == PATH_ORDERS.CUSTOM:
            raise Exception("not implemented")
        else:
            raise Exception("Invalid mode")

    def get_num_edges(self): 
        if self.path_mode == PATH_ORDERS.EDGE:
            return len(self.border_order_to_id_and_side_dict)
        elif self.path_mode == PATH_ORDERS.ALL:
            return len(self.monitor_ids) * 4
        elif self.path_mode == PATH_ORDERS.CUSTOM:
            return len(self.monitor_ids) * 4
        else:
            raise Exception("Invalid PATH_ORDER")

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
        
        if self.path_mode == PATH_ORDERS.EDGE:
            id_and_side_lookup = self.border_order_to_id_and_side_dict
        elif self.path_mode == PATH_ORDERS.ALL:
            id_and_side_lookup = self.complete_order_to_id_and_side_dict
        elif self.path_mode == PATH_ORDERS.CUSTOM:
            id_and_side_lookup = self.custom_order_to_id_and_side_dict
        else: raise Exception("Path mode was not valid")
        
        # print(id_and_side_lookup)
        
        for i in range(self.get_num_edges()):
            pid, side = id_and_side_lookup[i]
            row = self.get_pixel_row(pid, side)  # row will be empty if the monitor is not enabled

            if (self.path_mode == PATH_ORDERS.CUSTOM) and (self.custom_order_edge_directions[i] == -1):
                if side == 'u':
                    rgbrow = self.flip_row(row)
                elif side == 'd':
                    rgbrow = row
                elif side == 'l':
                    rgbrow = row
                elif side == 'r':
                    rgbrow = self.flip_row(row)
            else:
                if side == 'u':
                    rgbrow = row
                elif side == 'd':
                    rgbrow = self.flip_row(row)
                elif side == 'l':
                    rgbrow = self.flip_row(row)
                elif side == 'r':
                    rgbrow = row
                
                # logic here for states, todo. doing it here allows for easy "skips" later if we want to disable some rows
            for colorval in rgbrow:
                data.append(round(colorval[0]))
                data.append(round(colorval[1]))
                data.append(round(colorval[2]))
   
        remove_info_tokens(data)
        data.append(MICROCHIP_STOP_BYTE)
        return data

    @classmethod
    def flip_row(cls, row):
        reshaped = row.reshape(-1, 3)
        flip = np.flip(reshaped, axis=0)
        return flip