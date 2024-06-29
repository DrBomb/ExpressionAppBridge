import json, os, time

# Cal file check time. In seconds.
CAL_CHECK_PERIOD = 5

# Debug list
debug_entries = []

# Global default cal object
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

# List of valid blendshapes. These line up with the ones listed on the ExpressionApp
PERFECT_SYNC_BLENDSHAPES = [
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
    "mouthDimple_R",      # 30
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

# Valid calibration types
CAL_TYPES = ['interpolation', 'outputSnap', 'simple']

# A few error messages
def printInterpolationUsage(key):
    print(f"Missing configs for \"{key}\" cal type interpolation! Required items are 'minY', 'maxin', 'minOut' and 'maxOut'") 
def printSimpleUsage(key):
    print(f"Missing config for \"{key}\" cal type simple. Required item is 'max'")
def printOutputSnapUsage(key):
    print(f"Missing config for \"{key}\" cal type outputSnap. Required item is 'limit'")

DEFAULT_WINDOW_SIZE = 5

# Rolling Average helper
class RollingAvg:
    def __init__(self, size=DEFAULT_WINDOW_SIZE):
        self.data = [None for x in range(size)]
        self.idx = 0
        self.size = size
    def input(self, number):
        self.data[self.idx] = number
        self.idx = self.idx + 1
        if self.idx >= self.size:
            self.idx = 0
    def avg(self):
        if self.size == 1:
            return self.data[0]
        out = 0
        for i in self.data:
            if i is None:
                continue
            out = out + i
        return out/self.size

class TrackingInput:
    def __init__(self, tracking_data, cal_filepath, default_cal=DEFAULT_CAL, rolling_avg_size=DEFAULT_WINDOW_SIZE):
        # Internal tracking data
        self.tracking_data = tracking_data
        
        # Head rotation and head position is averaged to reduce jitter
        self.headrotavgs = [RollingAvg(), RollingAvg(), RollingAvg()]
        self.headposavgs = [RollingAvg(), RollingAvg(), RollingAvg()]
        
        # Cal data
        self.cal_filepath = cal_filepath
        self.__default_cal = default_cal
        self.cal_timestamp = None
        self.cal_lastcheck = None
        self.loadCal()
        self.cleanCal()
        
    def loadCal(self):
        ''' Load calibration file. Create if missing '''
        try:
            with open(self.cal_filepath) as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.config = self.__default_cal
            with open(self.cal_filepath, "w") as f:
                json.dump(self.config, f, indent=2)
        self.cal_timestamp = os.path.getmtime(self.cal_filepath)
        self.cal_lastcheck = time.time()
    def cleanCal(self):
        ''' Check for the calibration entries. Remove invalid ones '''
        # Check for eye callib, replace with default values if needed
        try:
            entry = self.config['eyes']['left']['maxRotation']
            entry = self.config['eyes']['left']['fullScale']
            entry = self.config['eyes']['right']['maxRotation']
            entry = self.config['eyes']['right']['fullScale']
        except (KeyError, TypeError):
            self.config['eyes'] = self.__default_cal['eyes']
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
            if k not in PERFECT_SYNC_BLENDSHAPES:
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
    def eyeRotation(self):
        """Calculate rotation values from stored blendshapes. Rotations are in degrees. No Up/Down rotation set."""
        
        # Left Eye parameters
        leftEye = self.tracking_data.blendshapes['eyeLookOut_L'] - self.tracking_data.blendshapes['eyeLookIn_L']
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
        rightEye = self.tracking_data.blendshapes['eyeLookIn_R'] - self.tracking_data.blendshapes['eyeLookOut_R']
        rightEyeFullScale = self.config['eyes']['right']['fullScale']
        rightEyeMaxRotation = self.config['eyes']['right']['maxRotation']
        
        # Cap raw value to the fullScale setting. Keep the sign
        if rightEye > rightEyeFullScale:
            rightEye = rightEyeFullScale
        if rightEye < rightEyeFullScale * -1:
            rightEye = rightEyeFullScale * -1
        
        # Set rotation for right eye
        self.tracking_data.rightEye[1] = (rightEye / rightEyeFullScale) * rightEyeMaxRotation
    def input_tracking(self, tracking_data):
        ''' Accept a tracking data object, apply calibration and save the result to the internal tracking_data '''
        
        # Check for cal changes and reload if needed
        if time.time() > self.cal_lastcheck + CAL_CHECK_PERIOD:
            self.cal_lastcheck = time.time()
            modtime = os.path.getmtime(self.cal_filepath)
            if modtime != self.cal_timestamp:
                print("Config file changed, reloading")
                self.loadCal()
                self.cleanCal()
                self.cal_timestamp = modtime
        
        # Save confidence
        self.tracking_data.confidence = tracking_data.confidence
        
        # Feed the head pos and rotation to their RollingAvg filters
        self.headrotavgs[0].input(tracking_data.head[0])
        self.headrotavgs[1].input(tracking_data.head[1])
        self.headrotavgs[2].input(tracking_data.head[2])
        self.headposavgs[0].input(tracking_data.head[3])
        self.headposavgs[1].input(tracking_data.head[4])
        self.headposavgs[2].input(tracking_data.head[5])
        
        # Save head rot and pos
        self.tracking_data.head[0] = self.headrotavgs[0].avg()
        self.tracking_data.head[1] = self.headrotavgs[1].avg()
        self.tracking_data.head[2] = self.headrotavgs[2].avg()
        self.tracking_data.head[3] = self.headposavgs[0].avg()
        self.tracking_data.head[4] = self.headposavgs[1].avg()
        self.tracking_data.head[5] = self.headposavgs[2].avg()
        
        # Copy blendshapes from source to destination
        for k, i in tracking_data.blendshapes.items():
            self.tracking_data.blendshapes[k] = i
        
        # Compute eye rotation data
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
            for d_k in debug_entries:
                if d_k in k:
                    print(f"{k} raw {rawValue} cal {calValue}")
            self.tracking_data.blendshapes[k] = int(round(calValue))
        
        # Handle now other debug entries that are not in cal
        for k, v in self.tracking_data.blendshapes.items():
            # Skip entries in calib
            if k in calKeys:
                continue
            for d_k in debug_entries:
                if d_k in k:
                    print(f"{k} {self.tracking_data.blendshapes[k]}")

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