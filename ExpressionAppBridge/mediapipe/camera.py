from pygrabber.dshow_graph import FilterGraph
import threading
import numpy as np

# Create camera graph, ask user for camera selection and resolution
def create_guided_camera_graph_flow(camera, camera_cap):
    # Instance PyGrabber graph
    graph = FilterGraph()
    
    if camera == None:
        # List cameras
        cameras = graph.get_input_devices()
        print("Available cameras")
        for i, k in enumerate(cameras):
            print(f"{i} - {k}")
        
        print("Select a camera")
        while True:
            try:
                camera = int(input("->"))
                if camera >= 0 and camera < len(cameras):
                    break
                print("Please select a number corresponding to a camera")
            except ValueError:
                print("Please select a number corresponding to a camera")
    
    # Add camera
    graph.add_video_input_device(camera)
    
    # Fetch available formats
    formats = graph.get_input_device().get_formats()
    
    if camera_cap == None:
        print("Available camera modes")
        for i, k in enumerate(formats):
            print(f"{i} - {k['width']}x{k['height']}@{int(k['max_framerate'])} {k['media_type_str']}")
        
        print("Select a camera mode")
        while True:
            try:
                camera_cap = int(input('->'))
                if camera_cap >= 0 and camera_cap < len(formats):
                    break
                print("Please select a number corresponding a camera mode")
            except ValueError:
                print("Please select a number corresponding a camera mode")
    
    graph.get_input_device().set_format(formats[camera_cap]['index'])
    
    return graph

# Create camera backend using guided workflow
def create_camera_backend(camera, camera_cap):
    return CameraBackend(create_guided_camera_graph_flow(camera, camera_cap))

class CameraBackend:
    def __init__(self, graph):
        self.graph = graph
        self.graph.add_sample_grabber(self.img_cb)
        self.graph.add_null_render()
        self.graph.prepare_preview_graph()
        self.graph.run()
        self.image_done = threading.Event()
        self.image_grabbed = None
    def img_cb(self, image):
        self.image_grabbed = image
        self.image_done.set()
    def read(self):
        self.image_done.clear()
        self.graph.grab_frame()
        ret = self.image_done.wait(1000)
        return ret, np.array(self.image_grabbed)