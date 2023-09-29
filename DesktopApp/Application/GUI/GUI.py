import tkinter as tk
import pystray
from pystray import MenuItem as item
import os
from PIL import Image

from ..utils import find_monitor_ids, get_n_borders
from .. import constants
from ..constants import PATH_ORDERS, ICON_PATH
from .DragDropFrame import DragDropFrame
from .CanvasGrid import CanvasGrid

class GUI:
    def __init__(self, orchestrator, settings, ser) -> None:
        self.orchestrator = orchestrator
        self.settings = settings
        self.ser = ser
        
        # make the structure
        self.window = tk.Tk()
        self.window.title("Boxman Fiddlejig")
        self.window.iconbitmap(ICON_PATH)
        self.canvases = []  # we might not need to save these just yet
        self.grids = []


        # monitor frame
        self.monitorframe = tk.Frame(self.window)
        for i, monitor_id in enumerate(find_monitor_ids()):
            frame = tk.Frame(self.monitorframe)
            self.canvases.append(tk.Canvas(frame))
            self.canvases[i].pack(expand=True, fill=tk.BOTH)
            self.grids.append(CanvasGrid(self.canvases[i], self.orchestrator.monitor_borders[i], self.orchestrator))

            c, r = orchestrator.get_monitor_grid_position_by_id(monitor_id)
            frame.grid(row=r, column=c, sticky=tk.NSEW)
            self.monitorframe.grid_columnconfigure(c, weight=1)
            self.monitorframe.grid_rowconfigure(r, weight=1)
        # 

        # options frame
        self.optionsframe = tk.Frame(self.window)
        
        ## options params frame
        self.options_params_frame = tk.Frame(self.optionsframe)

        ### ordering frame
        self.ordering_frame = tk.Frame(self.options_params_frame)

        self.radio_option_order_var = tk.IntVar()
        self.radio_option_order_var.set(self.settings.get_path_order_mode().value)
        self.radio_option_order_custom = tk.Radiobutton(self.ordering_frame, text="Custom ordering", font=('Helvetica 12 bold'), variable=self.radio_option_order_var, value=PATH_ORDERS.CUSTOM.value, command=self.ordering_radio_changed)
        self.radio_option_order_edges = tk.Radiobutton(self.ordering_frame, text="Auto outer edges", font=('Helvetica 12 bold'), variable=self.radio_option_order_var, value=PATH_ORDERS.EDGE.value, command=self.ordering_radio_changed)
        self.radio_option_order_all = tk.Radiobutton(self.ordering_frame, text="Auto all edges", font=('Helvetica 12 bold'), variable=self.radio_option_order_var, value=PATH_ORDERS.ALL.value, command=self.ordering_radio_changed)

        self.radio_option_order_custom.pack(side=tk.BOTTOM, anchor=tk.W)
        self.radio_option_order_edges.pack(side=tk.BOTTOM, anchor=tk.W)
        self.radio_option_order_all.pack(side=tk.BOTTOM, anchor=tk.W)
        self.ordering_radio_changed() # called to initialize the current state in settings
        ### 

        self.ordering_frame.pack(side=tk.LEFT)
        

        ### pixel width and height entry form
        self.pixelframe = tk.Frame(self.options_params_frame)
        
        self.v_pixelwidthentry = (self.window.register(self._callback_validate_and_handle_pixelwidthentry), '%P', '%d') 
        self.v_pixelheightentry = (self.window.register(self._callback_validate_and_handle_pixelheightentry), '%P', '%d')

        self.pixelwidthlabel = tk.Label(self.pixelframe, text="Pixel Width", font=('Helvetica 12 bold'))
        self.pixelwidthlabel.grid(row=0, column=0)
        self.pixelwidthentryvar = tk.StringVar()
        self.pixelwidthentryvar.set(settings.get_pixel_width())
        self.pixelwidthentry = tk.Entry(self.pixelframe, validate='key', validatecommand=self.v_pixelwidthentry, textvariable=self.pixelwidthentryvar)
        self.pixelwidthentry.grid(row=0, column=1)
        
        self.pixelheightlabel = tk.Label(self.pixelframe, text="Pixel Height", font=('Helvetica 12 bold'))
        self.pixelheightlabel.grid(row=1, column=0)
        self.pixelheightentryvar = tk.StringVar()
        self.pixelheightentryvar.set(settings.get_pixel_height())
        self.pixelheightentry = tk.Entry(self.pixelframe, validate='key', validatecommand=self.v_pixelheightentry, textvariable=self.pixelheightentryvar)
        self.pixelheightentry.grid(row=1, column=1)
        ### 

        self.pixelframe.pack(side=tk.LEFT)

        ### port selection frame
        self.portframe = tk.Frame(self.options_params_frame)
        self.com_port_options = ser.find_serial_ports()  # todo refactor into an update button that works
        self.com_port_selection = tk.StringVar()
        self.com_port_selection.trace_variable("w", self._callback_com_port_dropdown_selection_updated)

        self.com_port_selection.set(self.settings.get_last_com_port())
        self.com_port_dropdown = tk.OptionMenu(self.portframe, self.com_port_selection, *self.com_port_options)
        self.com_port_dropdown.pack(side=tk.BOTTOM)
        
        self.com_port_refresh_btn = tk.Button(self.portframe, text="Refresh Ports", font=('Helvetica 8 bold'), command=self.update_com_port_dropdown)
        self.com_port_refresh_btn.pack(side=tk.TOP)
        ### 

        self.portframe.pack(side=tk.LEFT)

        ### enabled monitors checkboxes frame
        self.enabled_monitors_frame = tk.Frame(self.options_params_frame)
        self.monitor_enabled_vars = []
        self.monitor_enabled_checks = []
        enabled_ids = self.settings.get_enabled_monitor_ids()
        for monitor_id in self.orchestrator.monitor_ids:
            var = tk.IntVar()
            chk = tk.Checkbutton(
                self.enabled_monitors_frame, 
                variable=var, 
                command=self._callback_a_monitors_activation_state_changed, 
                text="Enable Monitor " + str(monitor_id), 
                font=('Helvetica 8 bold')
            )
            if monitor_id in enabled_ids:
                var.set(1)

            chk.pack(side=tk.BOTTOM)
            
            self.monitor_enabled_vars.append(var)
            self.monitor_enabled_checks.append(chk)
        self.enabled_monitors_frame.pack(side=tk.LEFT)
        ### 
        
        self.options_params_frame.pack(side=tk.TOP)
    
        ### wire order frame
        self.wire_order_frame = tk.Frame(self.optionsframe)
        self.wire_order_dragndrop = DragDropFrame(self.wire_order_frame, get_n_borders(), self._callback_custom_order_or_direction_changed)
        self.wire_order_dragndrop.pack(side=tk.RIGHT, fill=tk.X)

            # initialize the state of the dragndrop tab
        order = self.settings.get_custom_path_order()
        directions = self.settings.get_custom_path_directions()
        self.wire_order_dragndrop.set_item_order(order)
        self.wire_order_dragndrop.set_item_directions(directions)
        self.orchestrator.generate_monitor_custom_path(order, directions)
        ### 

        self.wire_order_frame.pack(side=tk.BOTTOM)


        self.optionsframe.pack(expand=False, fill=tk.X)
        self.monitorframe.pack(expand=True, fill=tk.BOTH)
        # load the save file and set default values

        # Set the size of the window
        self.window.geometry("700x350")
        self.window.protocol('WM_DELETE_WINDOW', self.hide_window)   

    # def _create_monitor_frame(self, )

    def _callback_com_port_dropdown_selection_updated(self, var, index, mode):
            print("new port selected: ", self.com_port_selection.get())
            self.settings.set_last_com_port(self.com_port_selection.get())
            self.ser.connect(self.com_port_selection.get())

    def _callback_validate_and_handle_pixelwidthentry(self, entry, action_type) -> bool:
        result = GUI._enter_only_max_two_digits(entry, action_type)
        if result:
            print("Pixel width: ", entry)
            if len(entry) == 0: return result
            try:
                self.settings.set_pixel_width(int(entry))
            except:
                print("Warning: could not set pixel width entry.")
            self._the_pixel_dimensions_changed()
        return result

    def _callback_validate_and_handle_pixelheightentry(self, entry, action_type) -> bool:
        result = GUI._enter_only_max_two_digits(entry, action_type)
        if result:
            print("Pixel height: ", entry)
            if len(entry) == 0: return result
            try:
                self.settings.set_pixel_height(int(entry))
            except:
                print("Warning: could not set pixel height entry.")
            self._the_pixel_dimensions_changed()
        return result

    def _callback_a_monitors_activation_state_changed(self):
        print("Monitor enabled states changed!")
        enabled_ids = []
        for i, monitor_id in enumerate(self.orchestrator.monitor_ids):
            if self.monitor_enabled_vars[i].get():
                enabled_ids.append(monitor_id)
        self.settings.set_enabled_monitor_ids(enabled_ids)
        self.orchestrator.set_enabled_monitors(enabled_ids)

    def _callback_custom_order_or_direction_changed(self):
        print("_callback_custom_order_or_direction_changed reached!")
        order = self.wire_order_dragndrop.get_item_order()
        directions = self.wire_order_dragndrop.get_item_directions()
        self.settings.set_custom_path_order(order)
        self.settings.set_custom_path_directions(directions)
        self.orchestrator.generate_monitor_custom_path(order, directions)

    @staticmethod
    def _enter_only_max_two_digits(entry, action_type) -> bool:
        if action_type == '1' and not entry.isdigit():
            return False
        if action_type == '1' and float(entry) > 100:
            return False
        return True

    def _the_pixel_dimensions_changed(self):
        self.orchestrator.update_border_dimensions(
            self.settings.get_pixel_width(),
            self.settings.get_pixel_height()
        )
        for grid in self.grids: grid.initialize_objects()

    # Define a function for quit the window
    def quit_window(self, icon, item):
        constants.SOFTKILL_MODEL = True
        
        icon.stop()
        self.window.destroy()
        # exit()

    # Define a function to show the window again
    def show_window(self, icon, item):
        icon.stop()
        self.window.after(0, self.window.deiconify())

    # Hide the window and show on the system taskbar
    def hide_window(self):
        self.window.withdraw()
        image=Image.open(ICON_PATH)
        menu=(
            item('Quit', self.quit_window), 
            item('Show', self.show_window, default=True),)
        self.icon=pystray.Icon("name", image, "I control your LEDs", menu)
        self.icon.run()

    def update_com_port_dropdown(self):
        # com_port_selection.set('')
        self.com_port_dropdown['menu'].delete(0, 'end')
        new_choices = self.ser.find_serial_ports()
        for choice in new_choices:
            self.com_port_dropdown['menu'].add_command(label=choice, command=tk._setit(self.com_port_selection, choice))

    def ordering_radio_changed(self):
        selected_option = PATH_ORDERS(self.radio_option_order_var.get())
        self.settings.set_path_order_mode(selected_option)
        self.orchestrator.set_path_mode(selected_option)
        print("Selected option:", selected_option)
        
    def update_tk(self):
        self.window.update_idletasks()
        self.window.update()

    def update_grid(self):
        for grid in self.grids:
            grid.update()
