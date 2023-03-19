'''
ExpressionApp.py

Manage the ExpressionApp app.

Has a mapping that gives a name for each index to a perfect sync blendshape.

start_ExpressionApp is an asyncio coroutine that will start the ExpressionApp binary and listen for the data it sends and do a callback on every message
'''

import asyncio, os, json, subprocess
from config_utils import debug_settings

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
    "eyeLookout_L",       # 16
    "eyeLookout_R",       # 17
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

CAL_FILENAME = "ExpApp_Cal.json"
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

async def sendCommand(payload):
    loop = asyncio.get_running_loop()
    return await loop.create_datagram_endpoint(lambda: ExpressionAppSendProtocol(payload), remote_addr=('127.0.0.1', 9160))

async def expAppCal():
    print(f"Waiting {CAL_DELAY} seconds for callib")
    try:
        await asyncio.sleep(CAL_DELAY)
    except asyncio.CancelledError:
        return
    try:
        transport, protocol = await sendCommand('{"cmd":" calibrate"}'.encode())
    except asyncio.CancelledError:
        await transport.close()

async def start_ExpressionApp(config, onMessage, cal):
    """Start nvidia ExpressionApp and start the UDP listener to receive the parameters"""
    
    # Get the camera to be used
    camera = config.get('camera', 0)
    
    # Camera settings
    res = config.get('res', "1280x720")
    fps = config.get('fps', "30")
    
    # Open the cal file
    cal_file = loadCal()
    # Concat all cal coefficients with a semicolon
    cal_params = ";".join([f"{x:.6f}" for x in cal_file])
    
    # Call parameters
    parameters = [
        "--show=True",
        "--landmarks=True",
        f"--model_path={config['expapp_dir']}\models",
        f"--cam_res={res}",
        "--expr_mode=2",
        f"--camera={camera}",
        "--camera_cap=0",
        f"--cam_fps={fps}",
        f"--fps_limit={fps}",
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
            asyncio.create_task(expAppCal())
        
        while True:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        print("Closing ExpressionApp", flush=True)
        ExpressionApp_process.terminate()
        await ExpressionApp_process.wait()
        transport.close()