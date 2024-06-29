from sys import platform

if platform == "linux":
  import cv2
else:
  from ExpressionAppBridge.mediapipe.camera import create_camera_backend

from ExpressionAppBridge.tracking_data import TrackingData

import time, transforms3d, threading

# Math constants
ROT_X_FACTOR = 100
ROT_Y_FACTOR = -100
ROT_Z_FACTOR = -100
POS_X_FACTOR = -0.01
POS_Y_FACTOR = 0.01
POS_Z_FACTOR = 0.01

# Mapping from mediapipe parameters to iFM
# The mediapipe parameters seem to be mirrored so Left and Right are mapped opposite
mediapipe_to_ifm = {
    "browInnerUp": "browInnerUp",
    "browDownLeft": "browDown_R",
    "browDownRight": "browDown_L",
    "browOuterUpLeft": "browOuterUp_R",
    "browOuterUpRight": "browOuterUp_L",
    # Eye
    "eyeLookUpLeft": "eyeLookUp_R",
    "eyeLookUpRight": "eyeLookUp_L",
    "eyeLookDownLeft": "eyeLookDown_R",
    "eyeLookDownRight": "eyeLookDown_L",
    "eyeLookInLeft": "eyeLookIn_R",
    "eyeLookInRight": "eyeLookIn_L",
    "eyeLookOutLeft": "eyeLookOut_R",
    "eyeLookOutRight": "eyeLookOut_L",
    "eyeBlinkLeft": "eyeBlink_R",
    "eyeBlinkRight": "eyeBlink_L",
    "eyeSquintLeft": "eyeSquint_R",
    "eyeSquintRight": "eyeSquint_L",
    "eyeWideLeft": "eyeWide_R",
    "eyeWideRight": "eyeWide_L",
    # Cheek
    "cheekPuff": "cheekPuff",
    "cheekSquintLeft": "cheekSquint_R",
    "cheekSquintRight": "cheekSquint_L",
    # Nose
    "noseSneerLeft": "noseSneer_R",
    "noseSneerRight": "noseSneer_L",
    # Jaw
    "jawOpen": "jawOpen",
    "jawForward": "jawForward",
    "jawLeft": "jawRight",
    "jawRight": "jawLeft",
    # Mouth
    "mouthFunnel": "mouthFunnel",
    "mouthPucker": "mouthPucker",
    "mouthLeft": "mouthRight",
    "mouthRight": "mouthLeft",
    "mouthRollUpper": "mouthRollUpper",
    "mouthRollLower": "mouthRollLower",
    "mouthShrugUpper": "mouthShrugUpper",
    "mouthShrugLower": "mouthShrugLower",
    "mouthClose": "mouthClose",
    "mouthSmileLeft": "mouthSmile_R",
    "mouthSmileRight": "mouthSmile_L",
    "mouthFrownLeft": "mouthFrown_R",
    "mouthFrownRight": "mouthFrown_L",
    "mouthDimpleLeft": "mouthDimple_R",
    "mouthDimpleRight": "mouthDimple_L",
    "mouthUpperUpLeft": "mouthUpperUp_R",
    "mouthUpperUpRight": "mouthUpperUp_L",
    "mouthLowerDownLeft": "mouthLowerDown_R",
    "mouthLowerDownRight": "mouthLowerDown_L",
    "mouthPressLeft": "mouthPress_R",
    "mouthPressRight": "mouthPress_L",
    "mouthStretchLeft": "mouthStretch_R",
    "mouthStretchRight": "mouthStretch_L",
    "tongueOut": "tongueOut"
}

def process_BlendShapes_into_TrackingData(Blendshapes, tracking_data):
    for C in Blendshapes[0]:
        if C.category_name in mediapipe_to_ifm.keys():
            tracking_data.blendshapes[mediapipe_to_ifm[C.category_name]] = C.score * 100

def mediapipe_start(cal, iFM, camera, camera_cap):
    
    # Import mediapipe
    import mediapipe as mp
    
    # Running Constants
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode
    
    # Temporary tracking data storage
    temp_td = TrackingData()
    # mediapipe does not give us confidence
    temp_td.confidence = 100
    
    # FaceLandmarker payload
    FrameInfo = None
    FrameReady = threading.Event()
    
    # FaceLandmarker callback function
    def onDetect(DetectionResult, Image, Cnf):
        nonlocal FrameInfo
        nonlocal FrameReady
        FrameInfo = DetectionResult
        FrameReady.set()
    
    # Set landmarker options
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path="face_landmarker.task"),
        running_mode=VisionRunningMode.LIVE_STREAM,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        result_callback=onDetect)
    
    with FaceLandmarker.create_from_options(options) as landmarker:
        # Create camera backend
        if platform == "linux":
            print("Using OpenCV for camera")
            cap = cv2.VideoCapture(camera)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))

            print(width, height, fps)
        else:
            cap = create_camera_backend(camera, camera_cap)
        
        start = None
        try:
            while True:
                start = time.time()
                # Capture frame-by-frame
                ret, frame = cap.read()
                if not ret:
                    print("Can't receive frame (stream end?). Exiting ...")
                    break
                
                # Convert to mediapipe format
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                
                # Send to landmarker, timestamp in ms
                landmarker.detect_async(mp_image, int(time.perf_counter() * 1000))
                
                if FrameReady.is_set():
                    FrameReady.clear()
                    try:
                        affine = transforms3d.affines.decompose(FrameInfo.facial_transformation_matrixes[0])
                        translation = affine[0]
                        rotation_euler = transforms3d.euler.mat2euler(affine[1])
                        
                        temp_td.head[0] = rotation_euler[0] * ROT_X_FACTOR
                        temp_td.head[1] = rotation_euler[1] * ROT_Y_FACTOR
                        temp_td.head[2] = rotation_euler[2] * ROT_Z_FACTOR
                        
                        temp_td.head[3] = translation[0] * POS_X_FACTOR
                        temp_td.head[4] = translation[1] * POS_Y_FACTOR
                        temp_td.head[5] = translation[2] * POS_Z_FACTOR
                        
                        process_BlendShapes_into_TrackingData(FrameInfo.face_blendshapes, temp_td)
                        
                        cal.input_tracking(temp_td)
                        
                        payload = str(iFM)
                        iFM.udp_send()
                        print(f"Running... {int(1/(time.time() - start))} FPS", end='\r')
                    except IndexError:
                        pass
        except KeyboardInterrupt:
            print("Closing...")