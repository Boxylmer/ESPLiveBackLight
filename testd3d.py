
import d3dshot

d = d3dshot.create()
d.capture()
d.screenshot()

img = d.get_latest_frame()
img.show()
