import json, os, asyncio

# Some debug flags
debug_settings = {
    "debug_ifm": False,
    "debug_param": [],
    "debug_expapp": False
}

# Default calibration object
DEFAULT_CAL = {
    "eyes": {
        "left": {
            "maxRotation": 30,
            "fullScale": 80
        },
        "right": {
            "maxRotation": 30,
            "fullScale": 80
        }
    }
}

# Default iFM object
DEFAULT_IFM = {
    "port": 49983,
    "addr": "127.0.0.1"
}

# A few error messages
def printInterpolationUsage(key):
    print(f"Missing configs for {key} cal type interpolation! Required items are 'minY', 'maxin', 'minOut' and 'maxOut'") 
def printSimpleUsage(key):
    print(f"Missing config for {key} cal type simple. Required item is 'max'")
def printOutputSnapUsage(key):
    print(f"Missing config for {key} cal type outputSnap. Required item is 'limit'")


def doCal(config, in_ex):
    '''Apply calibration to the in_ex input'''
    out_ex = 0
    
    # Interpolation procedure
    if config['type'] == 'interpolation':
        Xin = in_ex
        minIn = config['minIn']
        maxIn = config['maxIn']
        minOut = config['minOut']
        maxOut = config['maxOut']
        if Xin < minIn:
            Xin = minIn
        if Xin > maxIn:
            Xin = maxIn
        out_ex = ((maxOut - minOut)/(maxIn - minIn) * (Xin - minIn)) + minOut
    
    # Simple procedure
    elif config['type'] == 'simple':
        Xin = in_ex
        max_in = config['max']
        if Xin > max_in:
            Xin = max_in
        out_ex = (Xin / max_in) * 100
    
    # OutputSnap procedure
    elif config['type'] == 'outputSnap':
        Xin = in_ex
        limit = config['limit']
        if Xin > limit:
            out_ex = 100
        else:
            out_ex = Xin
    return out_ex

CAL_TYPES = ['interpolation', 'outputSnap', 'simple']

def loadConfig(filepath):
    ''' Load config file, set default eyes cal and strip invalid blendshape cals'''
    
    # Load file
    with open(filepath) as f:
        config = json.load(f)
    
    # iFM config handling. Nothing too fancy.
    ifm = config.get('iFM')
    if ifm is None:
        print("iFM sender set to default values")
        config['iFM'] = DEFAULT_IFM
    else:
        try:
            print("iFM sender set to", ifm['addr'], ifm['port'])
        except KeyError:
            print("iFM settings are missing. Setting to default")
            config['iFM'] = DEFAULT_IFM
    
    # Get cal object
    cal = config.get('calibration')
    
    # Set default cal if missing
    if cal is None:
        config["calibration"] = DEFAULT_CAL
        cal = config['calibration']
    
    # Get eyes object
    eyes = cal.get('eyes')
    
    # Set default eyes if missing
    if eyes is None:
        cal['eyes'] = DEFAULT_CAL['eyes']
    
    # Get blendshape cals
    bs_cal = cal.get('blendshapes')
    
    if bs_cal is not None:
        # Check for dict
        if type(bs_cal) is not dict:
            print("Blendshape calibration is not a dictionary")
            
            # Remove blendshapes member from config
            cal.pop('blendshapes')
            
            return config
        
        # Iterate on a dict clone
        for k, i in dict(bs_cal).items():
            cal_type = i.get('type')
            
            # Check for cal type
            if cal_type is None:
                print(f"No cal type for {k}")
                bs_cal.pop(k)
                continue
            if cal_type not in CAL_TYPES:
                print(f"No valid type for {k}")
                bs_cal.pop(k)
                continue
            
            # Get the keys on the dict. Verify the parameters on it.
            cal_keys = list(i.keys())
            if cal_type == "interpolation":
                for arg in ['minIn', 'maxIn', 'minOut', 'maxOut']:
                    if arg not in cal_keys:
                        printInterpolationUsage(k)
                        bs_cal.pop(k)
                        break
            elif cal_type == 'outputSnap':
                if 'limit' not in cal_keys:
                    printOutputSnapUsage(k)
                    bs_cal.pop(k)
                    break
            elif cal_type == 'simple':
                if 'max' not in cal_keys:
                    printSimpleUsage(k)
                    bs_cal.pop(k)
                    break
    return config

# Coroutine that will check for the config file and reload it if modified
async def config_file_refresher(path, config_object):
    try:
        mod_time = os.path.getmtime(path)
        while True:
            this_time = os.path.getmtime(path)
            if mod_time != this_time:
                print("Config file changed, reloading")
                config_object |= loadConfig(path)
                mod_time = this_time
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        return