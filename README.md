# ESPLiveBackLight

This is a work in progress that uses 
- Python (TKinter, mss, and NumPy mainly)
- the ESP8266 Microcontroller (using the very well written FastLED library)
- the WS2812B led chip
- 3D printing through FreeCAD

To provide a fast, fully customizable backlight that updates with the colors on the borders of your screen.

It aims to consume as little CPU as possible and not compete with GPU resources. 

Features and todo

 - [X] Close to icon tray
 - [X] Consume less than 7% CPU with an AMD Ryzen 1600 and using 24FPS
 - [X] Allow full customize sequence for multiple monitors
 - [X] Automatically determine monitor orientation and locations
 - [ ] "Compile" and release ready-to-go binary
 - [ ] Finish 3D printed track design for easy backlight packaging
 - [ ] Finish KiCAD PCB design for more polished end product
 - [ ] Post writeup on construction and tutorial on assembly
