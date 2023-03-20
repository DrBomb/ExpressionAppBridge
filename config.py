import subprocess, re, os, json
from ExpressionAppBridge.config_utils import loadConfig

CAMERAINFO_FILE = "CameraInfo.json"

success_match = re.compile(r"Final camera configuration: (\d+)x(\d+) (\d+)")

color_space_match = re.compile(r"Color space: (\w+ \(\d+\))")

def match_stdout(text):
    res_match = success_match.search(text)
    color_match = color_space_match.search(text)
    
    res_result = f"{res_match.group(1)}x{res_match.group(2)}" if res_match is not None else None
    fps_result = int(res_match.group(3)) if res_match is not None else None
    
    color_result = color_match.group(1) if color_match is not None else None
    
    return res_result, fps_result, color_result

def check_cap(config, idx):
    parameters = [
        f"{config['expapp_dir']}\ExpressionApp.exe",
        f"--model_dir={config['expapp_dir']}\models",
        f"--camera_cap={idx}",
        f"--camera={config['camera']}",
    ]
    
    try:
        result = subprocess.run(parameters, capture_output=True, timeout=10)
        
        stdout = result.stdout.decode()
        
        res, fps, color = match_stdout(stdout)
    except subprocess.TimeoutExpired as e:
        print("Process Timeout")
        
        stdout = e.stdout.decode()
        
        res, fps, color = match_stdout(stdout)
    success = True if res is not None else False
    return success, res, fps, color

def checkAllCaps(config):
    caps_idx = 0
    caps_data = []
    
    while True:
        success, res, fps, color = check_cap(config, caps_idx)
        if not success:
            break
        caps_data.append([caps_idx, res, fps, color])
        print(f"Cap {caps_idx} {res} {fps} {color}")
        caps_idx = caps_idx + 1
    return caps_data

if __name__ == "__main__":
    config = loadConfig('ExpressionAppBridge\config.json')
    
    print("Starting config...")
    
    print("Current MXTracker dir:")
    print(config['expapp_dir'])
    
    print("Input a new path, leave empty to skip")
    
    while True:
        path = input("->")
        path.strip()
        if len(path) < 1:
            path = config['expapp_dir']
            break
        if os.path.isfile(os.path.join(path, "ExpressionApp.exe")):
            break
        print("ExpressionApp.exe not found in path!")
    
    config['expapp_dir'] = path
    
    try:
        with open("ExpressionAppBridge/CamInfo.json") as f:
            CamInfo = json.load(f)
    except FileNotFoundError:
        CamInfo = {}
    
    current = CamInfo.get("camera", "0")
    
    camera_input = None
    
    print(f"Current camera: {current}")
    
    print("Select camera number, leave empty to skip")
    
    while True:
        camera_input = input("->")
        camera_input.strip()
        if len(camera_input) < 1:
            camera_input = current
            break
        if type(int(camera_input)) is int:
            break
        print("Camera has to be an integer")
    
    CamInfo['camera'] = camera_input
    
    try:
        camera_details = CamInfo['CamInfo']
    except KeyError:
        CamInfo['CamInfo'] = {}
        camera_details = CamInfo['CamInfo']
    
    this_cam_info = camera_details.get(camera_input)
    
    if this_cam_info is None:
        print("Need to query all camera modes, this will take some time, please wait...")
        this_cam_info = checkAllCaps(config)
        camera_details[camera_input] = this_cam_info
        print("Saving camera details")
        with open("ExpressionAppBridge/CamInfo.json", "w") as f:
            json.dump(CamInfo, f, indent=2)
    
    print("Available camera modes:")
    for i, x in enumerate(this_cam_info):
        print(f"{i} - {x[1]} {x[2]} {x[3]}")
    
    print("Select a camera mode to set:")
    
    while True:
        cap_selection = input("->")
        try:
            cap_no = int(cap_selection)
        except ValueError:
            print("Please input the resolution you wish to use")
            continue
        break
    
    print(f"{this_cam_info[cap_no][1]} {this_cam_info[cap_no][2]} selected. Saving config...")
    config['camera'] = int(camera_input)
    config['res'] = this_cam_info[cap_no][1]
    config['fps'] = this_cam_info[cap_no][2]
    config['cam_cap'] = cap_no
    with open("ExpressionAppBridge\config.json", "w") as f:
        json.dump(config, f, indent=2)
    