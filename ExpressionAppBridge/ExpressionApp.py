'''
ExpressionApp.py

Manage the ExpressionApp app.

Has a mapping that gives a name for each index to a perfect sync blendshape.

start_ExpressionApp is an asyncio coroutine that will start the ExpressionApp binary and listen for the data it sends and do a callback on every message
'''

import asyncio, os, json, subprocess
from .config_utils import debug_settings, saveConfig

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

CAL_FILENAME = "ExpressionAppBridge\ExpApp_Cal.json"
CAL_DELAY = 10

def saveCal(cal):
    with open(CAL_FILENAME, "w") as f:
        json.dump(cal, f)
    print("Cal saved!")

def loadCal():
    try:
        with open(CAL_FILENAME) as f:
            return(json.load(f))
    except FileNotFoundError:
        return([])

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

async def start_ExpressionApp(config, camera_config, onMessage, cal):
    """Start nvidia ExpressionApp and start the UDP listener to receive the parameters"""
    
    # Open the cal file
    cal_file = loadCal()
    # Concat all cal coefficients with a semicolon
    cal_params = ";".join([f"{x:.6f}" for x in cal_file])
    
    # Call parameters
    parameters = [
        "--show=True",
        "--landmarks=True",
        f"--model_path={config['expapp_dir']}\models",
        f"--cam_res={camera_config['res']}",
        "--expr_mode=2",
        f"--camera={camera_config['camera']}",
        f"--camera_cap={camera_config['cap']}",
        f"--cam_fps={camera_config['fps']}",
        f"--fps_limit={camera_config['fps']}",
        "--use_opencl=False",
        "--cam_api=0"
    ]
    
    # Add calib parameters if loaded
    if len(cal_params) != 0:
        parameters.append(f"--expr_calibration={cal_params}")
    
    try:
        print("Opening ExpressionApp", flush=True)
        ExpressionApp_process = await asyncio.create_subprocess_exec(f"{config['expapp_dir']}\ExpressionApp.exe", *parameters, 
        stdout=None if debug_settings['debug_expapp'] else asyncio.subprocess.DEVNULL,
        stderr=None if debug_settings['debug_expapp'] else asyncio.subprocess.DEVNULL)
        
        print("Starting nvidia UDP listener")
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(lambda: ExpresssionAppProtocol(onMessage), local_addr=('127.0.0.1', 9140))
        
        # Request calibration if cal file is missing
        if len(cal_file) < 1 or cal:
            asyncio.create_task(expAppCal(camera_config['camera']))
        
        while True:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        print("Closing ExpressionApp", flush=True)
        ExpressionApp_process.terminate()
        await ExpressionApp_process.wait()
        transport.close()