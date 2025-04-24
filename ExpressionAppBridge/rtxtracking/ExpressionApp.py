'''
ExpressionApp.py

Manage the RTX Tracking ExpressionApp
'''

import asyncio, os, json, subprocess
from ..config_utils import debug_settings, saveConfig
from ..tracking_data import TrackingData
from ..quaternion import euler_from_quaternion
from math import sqrt

POSX_DIVIDER = 5000
POSY_DIVIDER = 5000
POSZ_DIVIDER = 2000

EXP_IDX_TO_PERFECT_SYNC = [
    "browDown_L",         # 0
    "browDown_R",         # 1
    "browInnerUp",        # 2 browInnerUp_L
    "browInnerUp",        # 3 browInnerUp_R - Average both
    "browOuterUp_L",      # 4
    "browOuterUp_R",      # 5
    "cheekPuff",          # 6 - cheekPuff_L
    "cheekPuff",          # 7 - cheekPuff_R - Average both
    "cheekSquint_L",      # 8
    "cheekSquint_R",      # 9
    "eyeBlink_L",         # 10
    "eyeBlink_R",         # 11
    "eyeLookDown_L",      # 12
    "eyeLookDown_R",      # 13
    "eyeLookIn_L",        # 14
    "eyeLookIn_R",        # 15
    "eyeLookOut_L",       # 16
    "eyeLookOut_R",       # 17
    "eyeLookUp_L",        # 18
    "eyeLookUp_R",        # 19
    "eyeSquint_L",        # 20
    "eyeSquint_R",        # 21
    "eyeWide_L",          # 22
    "eyeWide_R",          # 23
    "jawForward",         # 24
    "jawLeft",            # 25
    "jawOpen",            # 26
    "jawRight",           # 27
    "mouthClose",         # 28
    "mouthDimple_L",      # 29
    "mouthDimple_L",      # 30
    "mouthFrown_L",       # 31
    "mouthFrown_R",       # 32
    "mouthFunnel",        # 33
    "mouthLeft",          # 34
    "mouthLowerDown_L",   # 35
    "mouthLowerDown_R",   # 36
    "mouthPress_L",       # 37
    "mouthPress_R",       # 38
    "mouthPucker",        # 39
    "mouthRight",         # 40
    "mouthRollLower",     # 41
    "mouthRollUpper",     # 42
    "mouthShrugLower",    # 43
    "mouthShrugUpper",    # 44
    "mouthSmile_L",       # 45
    "mouthSmile_R",       # 46
    "mouthStretch_L",     # 47
    "mouthStretch_R",     # 48
    "mouthUpperUp_L",     # 49
    "mouthUpperUp_R",     # 50
    "noseSneer_L",        # 51
    "noseSneer_R"         # 52
]

CAL_FILENAME = "config/RTX_internal_cal.json"
CAL_DELAY = 10

# UDP Expressionapp protocol
class ExpresssionAppProtocol:
    def __init__(self, onMessage):
        self.onMessage = onMessage
        self.transport = None
    def connection_made(self, transport):
        self.transport = transport
        print("Expression App connected", flush=True)
    def datagram_received(self, data, addr):
        self.onMessage(data)
    def connection_lost(self, exc):
        pass

# UDP command sender
class ExpressionAppSendProtocol:
    def __init__(self, message):
        self.message = message
        self.transport = None
    def connection_made(self, transport):
        transport.sendto(self.message)
        transport.close()

async def sendCommand(payload, port):
    loop = asyncio.get_running_loop()
    return await loop.create_datagram_endpoint(lambda: ExpressionAppSendProtocol(payload), remote_addr=('127.0.0.1', port))

async def expAppCal(camera):
    print(f"Waiting {CAL_DELAY} seconds for callib")
    try:
        await asyncio.sleep(CAL_DELAY)
    except asyncio.CancelledError:
        return
    try:
        transport, protocol = await sendCommand('{"cmd":" calibrate"}'.encode(), 9160 + camera)
    except asyncio.CancelledError:
        await transport.close()

def formatStr(format_number):
    formats = dict([
        (0, "Any"),
        (1, "Unknown"),
        (100, "ARGB"),
        (101, "XRGB"),
        (102, "RGB24"),
        (200, "I420"),
        (201, "NV12"),
        (202, "YV12"),
        (203, "Y800"),
        (204, "P010"),
        (300, "YVYU"),
        (301, "YUY2"),
        (302, "UYVY"),
        (303, "HDYC"),
        (400, "MJPEG"),
        (401, "H264"),
        (402, "HEVC"),
    ])
    
    try:
        return formats[format_number]
    except KeyError:
        return formats[1]

def setup(config):
    save_config = False
    
    # Check for ExpressionApp.exe
    ExpAppPathInput = config.get('expapp_dir', "")
    while True:
        if not os.path.isfile(os.path.join(ExpAppPathInput, "ExpressionApp.exe")):
            save_config = True
            if ExpAppPathInput == "":
                print("There is no path set!")
            else:
                print(f"Path {ExpAppPathInput} does not contain ExpressionApp.exe!")
            print(f"Please input the path where ExpressionApp is located:")
            ExpAppPathInput = input("->").strip()
        else:
            print("ExpressionApp.exe found")
            break
    
    if save_config:
        config['expapp_dir'] = ExpAppPathInput
        saveConfig(config)
    
    run_parameters = [
        f"{ExpAppPathInput}\ExpressionApp.exe",
        "--print_caps"
    ]
    
    result = subprocess.run(run_parameters, capture_output=True)
    
    data = json.loads(result.stdout.decode().split("\r\n\r\n\r\n")[1])
    
    print("Available cameras")
    for c in data:
        print(f"{c['id']} - {c['name']}")
    
    print("Select a camera")
    while True:
        try:
            camera = int(input("->"))
            if camera >= 0 and camera < len(data):
                break
            print("Please select a number corresponding to a camera")
        except ValueError:
            print("Please select a number corresponding to a camera")
    
    print("Available camera modes")
    for i, c in enumerate(data[camera]['caps']):
        fps = int((1/(c['minInterval'])) * 10000000)
        codec = formatStr(c['format'])
        print(f"{i} - {c['maxCX']}x{c['maxCY']}@{fps} {codec}({c['format']})")
    
    print("Select a camera mode")
    while True:
        try:
            camera_cap = int(input('->'))
            if camera_cap >= 0 and camera_cap < len(data[camera]['caps']):
                break
            print("Please select a number corresponding a camera mode")
        except ValueError:
            print("Please select a number corresponding a camera mode")
    
    camera_conf = {
        "camera": camera,
        "cap": data[camera]['caps'][camera_cap]['id'],
        "res": f"{data[camera]['caps'][camera_cap]['maxCX']}x{data[camera]['caps'][camera_cap]['maxCY']}",
        "fps": int((1/(data[camera]['caps'][camera_cap]['minInterval'])) * 10000000)
    }
    
    return camera_conf

def convert_exp(expr_in):
    """ExpressionApp exp parameters are from 0 to 1. Convert to 0-100"""
    out = expr_in * 100
    if out > 100:
        return 100
    if out < 0:
        return 0
    return out

class ExpressionAppRunner:
    def __init__(self, cal_input, config, camera_config):
        # Internal container to parse data into
        self.parsed_data = TrackingData()
        
        # cal input in charge of consuming our parsed data
        self.cal = cal_input
        
        # Config file
        self.config = config
        
        # Config object generated from setup
        self.camera_config = camera_config
        
        # Center coords for passing pos data
        self.headCenter = [None, None, None]
    def loadCal(self):
        try:
            with open(CAL_FILENAME) as f:
                return(json.load(f))
        except FileNotFoundError:
            return([])
    def saveCal(self, cal):
        with open(CAL_FILENAME, "w") as f:
            json.dump(cal, f)
        print("Cal saved!")
    def headPos(self, pts):
        if len(pts)<254:
            return
        # Points for left and right side of face
        x1 = pts[2]
        y1 = pts[3]
        x2 = pts[66]
        y2 = pts[67]
        
        # Average X and Y to get a single position point
        x = (x2 + x1) / 2
        y = (y2 + y1) / 2
        
        # Get distance between points 1 and 2
        pointdist = sqrt((x2 - x1)**2 + (y2-y1)**2)
        
        # Store first position
        if self.headCenter[0] is None:
            self.headCenter = [x, y, pointdist]
        
        # Calculate pos values
        posx = (x - self.headCenter[0])/POSX_DIVIDER
        posy = (self.headCenter[1] - y)/POSY_DIVIDER
        posz = (pointdist - self.headCenter[2])/POSZ_DIVIDER
        
        # Store
        self.parsed_data.head[3] = posx
        self.parsed_data.head[4] = posy
        self.parsed_data.head[5] = posz
    def onMessage(self, message):
        """Parse message from ExpressionApp"""
        
        # JSON load
        data = json.loads(message[:-1].decode('utf-8'))
        
        # Check for cal message
        if len(data['cal']) > 0:
            self.saveCal(data['cal'])
            return
        
        # Save confidence
        self.parsed_data.confidence = data['cnf']
        
        # Parameter Elements
        head_rotation = data['rot']
        expressions = data['exp']
        
        # Point array
        points = data['pts']
        
        # Parse point data to get head position
        self.headPos(points)
        
        # Convert head rotation values
        hx, hy, hz = euler_from_quaternion(head_rotation[0], head_rotation[1], head_rotation[2], head_rotation[3])
        
        # Store head rotation values
        self.parsed_data.head[0] = hx
        self.parsed_data.head[1] = hy
        self.parsed_data.head[2] = hz
        
        # Fill in the tracking data blendshape data according to mapping. Skip indexes 2/3 and 6/7
        for i, x in enumerate(EXP_IDX_TO_PERFECT_SYNC):
            if i in [2, 3, 6, 7]:
                continue
            self.parsed_data.blendshapes[x] = convert_exp(expressions[i])
        
        # Handle 2/3 for browInner. Average them
        self.parsed_data.blendshapes['browInnerUp'] = (convert_exp(expressions[2]) + convert_exp(expressions[3]))/2
        
        # Handle 6/7 for cheekPuff same as browInner
        self.parsed_data.blendshapes['cheekPuff'] = (convert_exp(expressions[6]) + convert_exp(expressions[7]))/2
        
        # With all blendshape and head rotation data parsed, we call tracking input so cal values are applied
        self.cal.input_tracking(self.parsed_data)
    async def start(self, doCal):
        """Start nvidia ExpressionApp and start the UDP listener to receive the parameters"""
        # Open the cal file
        cal_file = self.loadCal()
        # Concat all cal coefficients with a semicolon
        cal_params = ";".join([f"{x:.6f}" for x in cal_file])
        
        # Call parameters
        parameters = [
            "--show=True",
            "--landmarks=True",
            f"--model_path={self.config['expapp_dir']}\models",
            f"--cam_res={self.camera_config['res']}",
            "--expr_mode=2",
            f"--camera={self.camera_config['camera']}",
            f"--camera_cap={self.camera_config['cap']}",
            f"--cam_fps={self.camera_config['fps']}",
            f"--fps_limit={self.camera_config['fps']}",
            "--use_opencl=False",
            "--cam_api=0"
        ]
        
        # Add calib parameters if loaded
        if len(cal_params) != 0:
            parameters.append(f"--expr_calibration={cal_params}")
        
        try:
            print("Opening ExpressionApp", flush=True)
            ExpressionApp_process = await asyncio.create_subprocess_exec(f"{self.config['expapp_dir']}\ExpressionApp.exe", *parameters, 
            stdout=None if debug_settings['debug_expapp'] else asyncio.subprocess.DEVNULL,
            stderr=None if debug_settings['debug_expapp'] else asyncio.subprocess.DEVNULL)
            
            print("Starting nvidia UDP listener")
            loop = asyncio.get_running_loop()
            transport, protocol = await loop.create_datagram_endpoint(lambda: ExpresssionAppProtocol(self.onMessage),
            local_addr=('127.0.0.1', 9140))
            
            # Request calibration if cal file is missing
            if len(cal_file) < 1 or doCal:
                asyncio.create_task(expAppCal(self.camera_config['camera']))
            
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            print("Closing ExpressionApp", flush=True)
            ExpressionApp_process.terminate()
            await ExpressionApp_process.wait()
            transport.close()