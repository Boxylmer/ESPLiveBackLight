import json
import os
from ..utils import get_n_borders
from ..constants import PATH_ORDERS

class Settings:
    PATH = "settings.json"
    DEFAULTJSON = '{"pathorder": 1, "pixel_width": 5, "pixel_height": 5, "last_com": null}'
    DEFAULT_DATA = json.loads(DEFAULTJSON)
    DEFAULT_DATA["enabled_monitor_ids"] = []
    DEFAULT_DATA["custom_path_order"] = [i for i in range(get_n_borders())]
    DEFAULT_DATA["custom_path_directions"] = [1 for _ in range(get_n_borders())]

    def __init__(self) -> None:
        if os.path.exists(Settings.PATH):
            with open(Settings.PATH, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = Settings.DEFAULT_DATA
            self.updatefile()

    def updatefile(self):
        with open(Settings.PATH, 'w') as json_file:
            json.dump(self.data, json_file)

    # getters
    def get_path_order_mode(self):
        return PATH_ORDERS(self.data["pathorder"])

    def get_custom_path_order(self):
        return self.data["custom_path_order"]
    
    def get_custom_path_directions(self):
        return self.data["custom_path_directions"]
    
    def get_pixel_width(self):
        return self.data["pixel_width"]
    
    def get_pixel_height(self):
        return self.data["pixel_height"]

    def get_last_com_port(self):
        return self.data["last_com"]

    def get_enabled_monitor_ids(self):
        return self.data["enabled_monitor_ids"]

    # setters
    def set_path_order_mode(self, mode):
        self.data["pathorder"] = mode.value
        self.updatefile()

    def set_custom_path_order(self, order):
        self.data["custom_path_order"] = order
        self.updatefile()

    def set_custom_path_directions(self, directions):
        self.data["custom_path_directions"] = directions
        self.updatefile()

    def set_pixel_width(self, width):
        self.data["pixel_width"] = width
        self.updatefile()
    
    def set_pixel_height(self, height):
        self.data["pixel_height"] = height
        self.updatefile()

    def set_last_com_port(self, port):
        self.data["last_com"] = port
        self.updatefile()

    def set_enabled_monitor_ids(self, ids):
        self.data["enabled_monitor_ids"] = ids
        self.updatefile()
