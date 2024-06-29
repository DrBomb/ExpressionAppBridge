import asyncio, signal, functools, json, argparse
from sys import platform
from ExpressionAppBridge.rtxtracking import ExpressionAppRunner, setup
from ExpressionAppBridge.mediapipe import mediapipe_start
from ExpressionAppBridge.iFM import iFM_Data, start_iFM_Sender
from ExpressionAppBridge.tracking_data import TrackingData
from ExpressionAppBridge.config_utils import loadConfig, debug_settings
from ExpressionAppBridge.cal import TrackingInput, debug_entries

async def rtx_main(args):
    # Load config file.
    config = loadConfig()
    
    # Test the ExpressionApp path, ask for camera settings
    camera_conf = setup(config)
    
    # Set up tracking storage
    tdata = TrackingData()
    
    # Set up iFM serializer
    iFM = iFM_Data(tdata)
    
    # Set up calibration
    cal = TrackingInput(tdata, "config/RTX_Blendshapes_cal.json")
    
    # Set up ExpressionApp
    expapp = ExpressionAppRunner(cal, config, camera_conf)
    
    # Run ExpressionApp and iFM sender
    await asyncio.gather(expapp.start(args.cal), start_iFM_Sender(iFM))

def mediapipe_main(args):
    # Set up tracking storage
    tdata = TrackingData()
    
    # iFM serializer
    iFM = iFM_Data(tdata)
    
    # Set up calibration
    cal = TrackingInput(tdata, "config/Mediapipe_Blendshapes_cal.json")
    
    # Start mediapipe main loop
    mediapipe_start(cal, iFM, args.camera, args.camera_cap)

if __name__ == "__main__":
    # Command line stuff
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', help="Camera index", action='store', type=int, required=platform == "linux")
    parser.add_argument('--camera-cap', help="Camera mode", action='store', type=int)
    if platform != "linux":
        parser.add_argument('--mode', choices=['rtx', 'mediapipe'])
    parser.add_argument('--debug-ifm', help="Print every iFM frame sent. VERY VERBOSE", action='store_true')
    parser.add_argument('--debug-expapp', help="Print tracker console output. Only for RTX", action='store_true')
    parser.add_argument('--debug-param', help="Provide a comma separated list of parameters to be printed IE. 'brow,blink'", action='store', metavar='param')
    parser.add_argument('--cal', action='store_true', help="Do a calibration on start. Only for RTX")
    
    # Parse command line args
    args = parser.parse_args()
    
    # Load command line args to debug struct
    debug_settings['debug_ifm'] = args.debug_ifm
    debug_entries = args.debug_param.split(',') if args.debug_param is not None else []
    debug_settings['debug_expapp'] = args.debug_expapp
    
    # Handle mode selection
    if platform != "linux":
        mode = args.mode
    else:
        mode = "mediapipe"
    
    if mode != 'rtx' and mode != 'mediapipe':
        mode = None
    
    # Or ask for it if not selected
    if mode is None:
        print("Select mode:")
        print("0 - Mediapipe tracking")
        print("1 - RTX tracking")
        while True:
            mode = input('->')
            if mode == '0':
                mode = 'mediapipe'
                break
            elif mode == '1':
                mode = 'rtx'
                break
            else:
                print("Please select with 0 or 1")
    
    if mode == 'rtx':
        # Launch rtx tracking
        try:
            asyncio.run(rtx_main(args))
        except KeyboardInterrupt:
            pass
    elif mode == 'mediapipe':
        # Launch mediapipe tracking
        mediapipe_main(args)