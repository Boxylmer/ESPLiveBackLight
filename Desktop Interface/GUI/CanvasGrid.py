import tkinter as tk

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
        if not self.mbpv.enabled: result = "-"
        elif result == None: result = "-"
        # elif result == 0: result = "start here!"
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
        self.canvas.coords(self.left_text, self._pixel_coords(0, "LEFT")[2], self.canvas.winfo_height()/2)
        self.canvas.coords(self.right_text, self._pixel_coords(0, "RIGHT")[0], self.canvas.winfo_height()/2)

        
        self.canvas.itemconfigure(self.top_text, text=self._get_side_text('u'))
        self.canvas.itemconfigure(self.bottom_text, text=self._get_side_text('d'))
        self.canvas.itemconfigure(self.left_text, text=self._get_side_text('l'))
        self.canvas.itemconfigure(self.right_text, text=self._get_side_text('r'))