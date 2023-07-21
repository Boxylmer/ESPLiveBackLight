import tkinter as tk
def _empty_callback(*args, **kwargs):
        pass


class DragDropItem(tk.Canvas):
    def __init__(self, parent, dragdropframe, item_id, **kwargs):
        super().__init__(parent, **kwargs)
        self.item_id = item_id
        self.dragdropframe = dragdropframe
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.release_drag)

        # track item directions! 
        self.arrow_direction = '→'


        w = int(self.cget('width'))
        h = int(self.cget('height'))
        bwidth = int(self.cget('borderwidth'))
        self.create_text(w/2 + 2 + bwidth, h/2.5 + 2 + bwidth, text=str(item_id), font='Helvetica 16 bold', anchor="center")
        self.arrow_widget = self.create_text(w/2 + 2 + bwidth, h * 0.9, text=self.arrow_direction, font='Helvetica 16 bold', anchor="center")

        self.actually_dragged = False # will use this later to check whether the user clicked + dragged + released or just clicked + released


    def toggle_arrow(self):
        if self.arrow_direction == '←':
            self.arrow_direction = '→'
        else:
            self.arrow_direction = '←'
        self.itemconfig(self.arrow_widget, text=self.arrow_direction)

    def start_drag(self, event):
        self._drag_data = {'x': event.x, 'y': event.y}
        self.actually_dragged = False

    def drag(self, event):
        delta_x = event.x - self._drag_data['x']
        delta_y = event.y - self._drag_data['y']
        self.place(x=self.winfo_x() + delta_x, y=self.winfo_y() + delta_y)
        self.actually_dragged = True

    def release_drag(self, event):
        self._drag_data = None
        if not self.actually_dragged:
            self.toggle_arrow()
        self.dragdropframe.order_updated()

    def get_direction(self):
        if self.arrow_direction == '→': return 1
        else: return -1

    def set_direction(self, direction):
        if self.arrow_direction == '→' and direction == 1:
            return
        elif self.arrow_direction == '←' and direction == -1:
            return
        else:
            self.toggle_arrow()

ITEMSIZE = 25
BORDERWIDTH = 2

class DragDropFrame(tk.Frame):
    def __init__(self, parent, item_count, callback_fn=_empty_callback):
        super().__init__(parent)
        self.are_locations_initialized = False
        self.item_count = item_count
        self.callback_fn = callback_fn
        self.items = []  # this is always in the same order
        self.item_id_order = range(0, self.item_count) # todo let the user specify this manually later

        self.canvas = tk.Canvas(self, width=(ITEMSIZE + 2 * BORDERWIDTH) * (item_count + 1) , height=ITEMSIZE + BORDERWIDTH * 2)
        self.canvas.pack(expand=True)

        self._create_items()
        self.update_locations()

    def _create_items(self):
        for i in self.item_id_order:
            item = DragDropItem(self.canvas, item_id=i, dragdropframe=self, relief=tk.SOLID, borderwidth=BORDERWIDTH, width=ITEMSIZE, height=ITEMSIZE, bg="white")
            self.items.append(item)

    def get_item_location(self, item):
        x = self.canvas.winfo_width()
        y = self.canvas.winfo_height()
        item_x = item.winfo_x()
        item_y = item.winfo_y()
        relative_x = item_x / x
        relative_y = item_y / y
        return relative_x, relative_y

    def set_item_location(self, item, relative_x, relative_y):
        x = self.canvas.winfo_width()
        y = self.canvas.winfo_height()
        item_x = relative_x * x
        item_y = relative_y * y
        item.place(x=item_x, y=item_y)

    def order_updated(self):
        self.compute_item_order()
        print(self.item_id_order)
        self.update_locations()
        self.callback_fn()

    def compute_item_order(self):
        sorted_items = sorted(self.items, key=lambda item: item.winfo_x())
        self.item_id_order = [item.item_id for item in sorted_items]

    def get_item_order(self):
        return self.item_id_order

    def set_item_order(self, order):
        if len(self.item_id_order) == len(order):
            self.item_id_order = order
        else:
            temp_order = [val for val in order if val < len(self.item_id_order)]
            while len(temp_order) < len(self.item_id_order):
                missing_val = max(temp_order) + 1 if temp_order else 0
                temp_order.append(missing_val)
            self.item_id_order = temp_order
        self.update_locations()

    def get_item_directions(self):
        return [item.get_direction() for item in self.items]
    
    def set_item_directions(self, directions):         
        for i, direction in enumerate(directions):  # will ignore all directions after len(self.items) has been passed. 
            self.items[i].set_direction(direction)

        if  len(directions) < len(self.items):
            # Pad the latter items
            for i in range(len(directions), len(self.items)):
                self.items[i].set_direction(1)  # You can replace '1' with the default direction for padding.

    def update_locations(self):
        spacing_x = 1 / (self.item_count)
        for i, item_id in enumerate(self.item_id_order):
            relative_x = i * spacing_x 
            relative_y = 0  
            self.set_item_location(self.items[item_id], relative_x, relative_y)

    def initialize_locations(self):
        self.update_locations()
        self.are_locations_initialized = True
    
    def needs_initialization(self): 
        return not self.are_locations_initialized
    

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Drag and Drop Program")
    root.geometry("800x600")


    # Create dummy widgets to cover the bottom half and right half of the screen
    bottom_half = tk.Frame(root, bg="red")
    bottom_half.place(relx=0, rely=0.5, relwidth=1, relheight=0.5)

    right_half = tk.Frame(root, bg="blue")
    right_half.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
    
    drag_drop_frame = DragDropFrame(root, item_count=10, )
    drag_drop_frame.pack( expand=True, side=tk.RIGHT)

    drag_drop_frame.items[2].set_direction(-1)
    assert(drag_drop_frame.items[2].get_direction() == -1)
    drag_drop_frame.items[2].set_direction(1)

    drag_drop_frame.items[1].set_direction(1)

    drag_drop_frame.set_item_directions([1, -1, 1, -1, 1, -1, 1, -1, 1, -1])


    root.mainloop()

