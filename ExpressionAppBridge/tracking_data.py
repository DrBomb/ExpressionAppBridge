'''
tracking_data.py

Tracking data storage. Contains blendshape, eye rotation, head pos and head rotation.
'''
class TrackingData:
    def __init__(self):
        """Perfect Sync Tracking parameters"""
        self.blendshapes = {
            # Brow
            "browInnerUp": 0,
            "browDown_L": 0,
            "browDown_R": 0,
            "browOuterUp_L": 0,
            "browOuterUp_R": 0,

            # Eye
            "eyeLookUp_L": 0,
            "eyeLookUp_R": 0,
            "eyeLookDown_L": 0,
            "eyeLookDown_R": 0,
            "eyeLookIn_L": 0,
            "eyeLookIn_R": 0,
            "eyeLookOut_L": 0,
            "eyeLookOut_R": 0,
            "eyeBlink_L": 0,
            "eyeBlink_R": 0,
            "eyeSquint_L": 0,
            "eyeSquint_R": 0,
            "eyeWide_L": 0,
            "eyeWide_R": 0,

            # Cheek
            "cheekPuff": 0,
            "cheekSquint_L": 0,
            "cheekSquint_R": 0,

            # Nose
            "noseSneer_L": 0,
            "noseSneer_R": 0,
            
            # Jaw
            "jawOpen": 0,
            "jawForward": 0,
            "jawLeft": 0,
            "jawRight": 0,

            # Mouth
            "mouthFunnel": 0,
            "mouthPucker": 0,
            "mouthLeft": 0,
            "mouthRight": 0,
            "mouthRollUpper": 0,
            "mouthRollLower": 0,
            "mouthShrugUpper": 0,
            "mouthShrugLower": 0,
            "mouthClose": 0,
            "mouthSmile_L": 0,
            "mouthSmile_R": 0,
            "mouthFrown_L": 0,
            "mouthFrown_R": 0,
            "mouthDimple_L": 0,
            "mouthDimple_R": 0,
            "mouthUpperUp_L": 0,
            "mouthUpperUp_R": 0,
            "mouthLowerDown_L": 0,
            "mouthLowerDown_R": 0,
            "mouthPress_L": 0,
            "mouthPress_R": 0,
            "mouthStretch_L": 0,
            "mouthStretch_R": 0,
            "tongueOut": 0
    }
        # Head rotation and position
        # RotX, RotY, RotZ, PosX, PosY, PosZ
        # Degrees
        self.head = [0, 0, 0, 0, 0, 0]
        # Right and Left eyes rotation
        # RotX, RotY, RotZ
        self.rightEye = [0, 0, 0]
        self.leftEye = [0, 0, 0]
        # Confidence indicator from ExpApp
        self.confidence = 0