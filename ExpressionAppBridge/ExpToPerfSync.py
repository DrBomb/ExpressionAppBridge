'''
ExpToPerfSync.py

Translation layer that will set the tracking data from ExpressionApp.

Takes care or receving the message callbacks from ExpressionApp, calulating eye rots, head rot, head pos and
applying any calibration present in the config file.
'''
import json, os, asyncio
from .quaternion import euler_from_quaternion
from .ExpressionApp import EXP_IDX_TO_PERFECT_SYNC, saveCal
from .config_utils import debug_settings
from math import sqrt

BS_CONFIG_FILEPATH = os.path.join(os.path.dirname(__file__), "BSCal.json")
AVG_SIZE = 5

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
    },
    "blendshapes": {}
}

def convert_exp(expr_in):
    """ExpressionApp exp parameters are from 0 to 1. Convert to 0-100"""
    out = expr_in * 100
    if out > 100:
        return 100
    if out < 0:
        return 0
    return out

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

class RollingAvg:
    def __init__(self, size):
        self.data = [None for x in range(size)]
        self.idx = 0
        self.size = size
    def input(self, number):
        self.data[self.idx] = number
        self.idx = self.idx + 1
        if self.idx >= self.size:
            self.idx = 0
    def avg(self):
        out = 0
        for i in self.data:
            if i is None:
                continue
            out = out + i
        return out/self.size

# A few error messages
def printInterpolationUsage(key):
    print(f"Missing configs for \"{key}\" cal type interpolation! Required items are 'minY', 'maxin', 'minOut' and 'maxOut'") 
def printSimpleUsage(key):
    print(f"Missing config for \"{key}\" cal type simple. Required item is 'max'")
def printOutputSnapUsage(key):
    print(f"Missing config for \"{key}\" cal type outputSnap. Required item is 'limit'")

CAL_TYPES = ['interpolation', 'outputSnap', 'simple']

class ExpToPerfSync:
    def __init__(self, tracking_data, **kwargs):
        self.tracking_data = tracking_data
        self.headCenter = [None, None, None]
        self.headrotavgs = [RollingAvg(AVG_SIZE), RollingAvg(AVG_SIZE), RollingAvg(AVG_SIZE)]
        self.headposavgs = [RollingAvg(AVG_SIZE), RollingAvg(AVG_SIZE), RollingAvg(AVG_SIZE)]
        self.config = None
        self.loadConfig()
    def verifyConfig(self):
        # Check for eye callib, replace with default values if needed
        try:
            entry = self.config['eyes']['left']['maxRotation']
            entry = self.config['eyes']['left']['fullScale']
            entry = self.config['eyes']['right']['maxRotation']
            entry = self.config['eyes']['right']['fullScale']
        except (KeyError, TypeError):
            self.config['eyes'] = DEFAULT_CAL['eyes']
            print("Reset eye cal to default")
        
        # Get blendshape entry
        bs_cal = self.config.get('blendshapes')
        
        # Exit if 'blendshape' is missing
        if bs_cal is None:
            return
        
        # Remove 'blendshapes' if it is not a dict
        if type(bs_cal) is not dict:
            self.config.pop('blendshapes')
            return
        
        # Iterate on a dict clone
        for k, i in dict(bs_cal).items():
            # Check if k is on the list
            if k not in EXP_IDX_TO_PERFECT_SYNC:
                print(f"\"{k}\" is not a valid Perfect Sync blendshape")
                bs_cal.pop(k)
            
            cal_type = i.get('type')
            
            # Check for cal type
            if cal_type is None:
                print(f"No cal type for \"{k}\"")
                bs_cal.pop(k)
                continue
            if cal_type not in CAL_TYPES:
                print(f"No valid type for \"{k}\"")
                bs_cal.pop(k)
                continue
            
            # Get the keys on the dict. Verify the parameters on it.
            cal_keys = list(i.keys())
            if cal_type == "interpolation":
                for arg in ['minIn', 'maxIn', 'minOut', 'maxOut']:
                    if arg not in cal_keys:
                        printInterpolationUsage(k)
                        bs_cal.pop(k)
                        continue
            elif cal_type == 'outputSnap':
                if 'limit' not in cal_keys:
                    printOutputSnapUsage(k)
                    bs_cal.pop(k)
                    continue
            elif cal_type == 'simple':
                if 'max' not in cal_keys:
                    printSimpleUsage(k)
                    bs_cal.pop(k)
                    continue
        
    def loadConfig(self):
        try:
            with open(BS_CONFIG_FILEPATH) as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.config = DEFAULT_CAL
            with open(BS_CONFIG_FILEPATH, "w") as f:
                json.dump(self.config, f, indent=2)
        self.verifyConfig()
        
    async def start_config_watcher(self):
        try:
            mod_time = os.path.getmtime(BS_CONFIG_FILEPATH)
            while True:
                this_time = os.path.getmtime(BS_CONFIG_FILEPATH)
                if mod_time != this_time:
                    print("Config file changed, reloading")
                    self.loadConfig()
                    mod_time = this_time
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            return
    def eyeRotation(self):
        """Calculate rotation values from stored blendshapes. Rotations are in degrees. No Up/Down rotation set."""
        
        # Left Eye parameters
        leftEye = self.tracking_data.blendshapes['eyeLookout_L'] - self.tracking_data.blendshapes['eyeLookout_R']
        leftEyeFullScale = self.config['eyes']['left']['fullScale']
        leftEyeMaxRotation = self.config['eyes']['left']['maxRotation']
        
        # Cap raw value to the fullScale setting. Keep the sign
        if leftEye > leftEyeFullScale:
            leftEye = leftEyeFullScale
        if leftEye < leftEyeFullScale * -1:
            leftEye = leftEyeFullScale * -1
        
        # Set rotation for left eye
        self.tracking_data.leftEye[1] = (leftEye / leftEyeFullScale) * leftEyeMaxRotation
        
        
        # Right Eye parameters
        rightEye = self.tracking_data.blendshapes['eyeLookIn_R'] - self.tracking_data.blendshapes['eyeLookout_R']
        rightEyeFullScale = self.config['eyes']['right']['fullScale']
        rightEyeMaxRotation = self.config['eyes']['right']['maxRotation']
        
        # Cap raw value to the fullScale setting. Keep the sign
        if rightEye > rightEyeFullScale:
            rightEye = rightEyeFullScale
        if rightEye < rightEyeFullScale * -1:
            rightEye = rightEyeFullScale * -1
        
        # Set rotation for right eye
        self.tracking_data.rightEye[1] = (rightEye / rightEyeFullScale) * rightEyeMaxRotation
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
        posx = (x - self.headCenter[0])/5000
        posy = (self.headCenter[1] - y)/5000
        posz = (pointdist - self.headCenter[2])/2000
        
        # Add to avg
        self.headposavgs[0].input(posx)
        self.headposavgs[1].input(posy)
        self.headposavgs[2].input(posz)
        
        self.tracking_data.head[3] = self.headposavgs[0].avg()
        self.tracking_data.head[4] = self.headposavgs[1].avg()
        self.tracking_data.head[5] = self.headposavgs[2].avg()
        
    def parseExpressionAppMessage(self, message):
        """Parse message from ExpressionApp"""
        
        # JSON load
        data = json.loads(message[:-1].decode('utf-8'))
        
        # Check for cal message
        if len(data['cal']) > 0:
            saveCal(data['cal'])
            return
        
        # Save confidence
        self.tracking_data.confidence = data['cnf']
        
        # Parameter Elements
        head_rotation = data['rot']
        expressions = data['exp']
        
        # Point array
        points = data['pts']
        
        # Parse point data to get head position
        self.headPos(points)
        
        # Convert head rotation values
        hx, hy, hz = euler_from_quaternion(head_rotation[0], head_rotation[1], head_rotation[2], head_rotation[3])
        
        self.headrotavgs[0].input(hx)
        self.headrotavgs[1].input(hy)
        self.headrotavgs[2].input(hz)
        self.tracking_data.head[0] = self.headrotavgs[0].avg()
        self.tracking_data.head[1] = self.headrotavgs[1].avg()
        self.tracking_data.head[2] = self.headrotavgs[2].avg()
        
        # Fill in the tracking data blendshape data according to mapping. Skip indexes 2/3 and 6/7
        for i, x in enumerate(EXP_IDX_TO_PERFECT_SYNC):
            if i in [2, 3, 6, 7]:
                continue
            self.tracking_data.blendshapes[x] = convert_exp(expressions[i])
        
        # Handle 2/3 for browInner. Average them
        self.tracking_data.blendshapes['brownInnerUp'] = (convert_exp(expressions[2]) + convert_exp(expressions[3]))/2
        
        # Handle 6/7 for cheekPuff same as browInner
        self.tracking_data.blendshapes['cheekPuff'] = (convert_exp(expressions[6]) + convert_exp(expressions[7]))/2
        
        # VSF does not use the eyelook parameters on the iFM frame. We need to translate those into rotation values
        self.eyeRotation()
        
        # Get target blendshapes for cal
        calKeys = (self.config.get('blendshapes', {}).keys())
        
        # Now apply any extra calibration entries on the config
        for k in calKeys:
            rawValue = self.tracking_data.blendshapes.get(k)
            if rawValue is None:
                print("No blendshape called", k)
                continue
            calValue = doCal(self.config['blendshapes'][k], rawValue)
            # Handle cal debug messages
            for d_k in debug_settings['debug_param']:
                if d_k in k:
                    print(f"{k} raw {rawValue} cal {calValue}")
            self.tracking_data.blendshapes[k] = int(round(calValue))
        
        # Handle now other debug entries that are not in cal
        for k, v in self.tracking_data.blendshapes.items():
            # Skip entries in calib
            if k in calKeys:
                continue
            for d_k in debug_settings:
                if d_k in k:
                    print(f"{k} {self.tracking_data.blendshapes[k]}")