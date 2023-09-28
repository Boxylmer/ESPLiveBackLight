from Application.constants import sct
from Application.constants import MICROCHIP_STOP_BYTE


def find_monitor_ids():
    return [*range(1, len(sct.monitors))]

def get_n_borders():
    return len(find_monitor_ids()) * 4

def remove_info_tokens(arr):
    """Remove all tokens from the bytearray that would otherwise have signal meaning, such as the sequence terminator token."""
    for i in range(1, len(arr) - 1):
        if arr[i] == MICROCHIP_STOP_BYTE:
            arr[i] = MICROCHIP_STOP_BYTE - 1 # clip to 254 and 0
        # we won't need to deal with the start byte as the server won't be watching for it during reading



def top_left_corner(id):
    return sct.monitors[id]["left"], sct.monitors[id]["top"]
def bottom_left_corner(id):
    return sct.monitors[id]["left"], sct.monitors[id]["top"] + sct.monitors[id]["height"]
def top_right_corner(id):
    return sct.monitors[id]["left"] + sct.monitors[id]["width"], sct.monitors[id]["top"]
def bottom_right_corner(id):
    return sct.monitors[id]["left"] + sct.monitors[id]["width"], sct.monitors[id]["top"] + sct.monitors[id]["height"]

