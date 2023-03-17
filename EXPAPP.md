## ExpressionApp.exe
 * ExpressionApp.exe is the executable invoked by VTube Studio.
 * The binary seems to be a modification of Nvidia's sample ExpressionApp, most likely the network interface was added, also it seems like keyboard control was stripped from it. This is the version it seems to be based on https://github.com/NVIDIA/MAXINE-AR-SDK/blob/cf68600c4f4da81425f8a7e706951fbb681d0e2f/samples/ExpressionApp/ExpressionApp.cpp
 * The binary dir contains a `models` folder with a bunch of files that I guess are the AI models.
 * The app sends UDP packets to localhost at port 9140 with a JSON format.
 * It seems to be sending to multiple ports, from 9140 to 9145
 * VTube Studio has a calibration button. At this path `<VTubeStudioDir>\VTube Studio_Data\StreamingAssets\Config\webcam_calibration_mx.json` there is a config json that contains the resulting callibration values. Values are passed as arguments to the binary.
 * Calibration can be set on runtime, the window can be hidden as well
 * Seems like all features detected on ExpressionApp are based on Perfect Sync blendshapes.
 * The binary has a `--help` flag but there is still too little information.

## Starting ExpressionApp

To start ExpressionApp open a command line prompt inside its folder located at `<VTubeStudioDir>\VTube Studio_Data\StreamingAssets\MXTracker` and use the command

`ExpressionApp.exe --show=True --landmarks=True --model_path=.\models --cam_res=1280x720 --expr_mode=2 --camera=0 --camera_cap=0 --cam_fps=30 --fps_limit=30 --use_opencl=False --cam_api=0`

This is how VTube Studio opens the program.

## Tracking JSON format
 * Packets sent via UDP, the app will send them even if there is no receiver
 * Sent to UDP ports 9140 thru 9145
 * The packet contains a trailing NULL char that needs to be removed before parsing the JSON
 * The data is a JSON dict
 * Key `exp` contains a 53 long array with parameters concerning expression detection. Values go from 0 to 1
 * Key `cal` is an empty array
 * Key `rot` has head rotation in quaternion x,y,z,w
 * Key `pos` has a 3 member array full of zeros. Surely for head position at some point.
 * Key `pts` has a 254 member array. It seems to contain the tracking points shown on the VTube Studio app. The points are X and Y points starting at index 2. Points 0 and 1 are the values for the camera capture resolution. It will send an empty array if the tracker loses enough confidence
 * Key `shw` maybe reports if the features window is shown
 * Key `cam` maybe reports the camera in use. 0 being the first one.
 * Key `fps` self explanatory
 * Key `num` no idea
 * Key `cnf` could be the "confidence" number shown in VTube Studio. Seems to be moving up to 50.

## Control JSON format

The app listens to UDP port 9160

### Landmark window control

*Hide*
`{"cmd":" hide_preview"}`

*Show*
`{"cmd":" show_preview"}`

### Calibration control

Sending the payload

`{"cmd":" calibrate"}`

Will trigger a message to the usual ports with some of the members empty but with the `cal` array populated

## Expression Parameters contents

The array that resides in `exp` seems to be the exact same order listed on this sample file https://github.com/NVIDIA/MAXINE-AR-SDK/blob/cf68600c4f4da81425f8a7e706951fbb681d0e2f/samples/ExpressionApp/ExpressionApp.cpp#L469

## Head position
As the `pos` member on the payload has just zeros. Head tracking has to be done differently.

For our tracking, we grab point 1 and point 33 which are the starting and ending points of the jawline. X and Y positions are averaged between both points. On start we record a center position.

For Z tracking we calculate the absolute distance between the two points. We also record the starting value.

Seems like moving the brows up registers as a right upwards rotation on the head. Consider compensating for it.

## ExpressionApp Limitations and Issues
ExpresssionApp does not seem to be able to detect "tongueOut". It also has "puffCheeks" parameters but they do not seem to be working that well. The latest version has a beta feature for reenabling detecting puffed cheeks

Overall although it has all Perfect Sync blendshapes sans tongueOut, the blendshapes seem to be affected by one another, such as one eye closing affecting the opposite.

Our own fork of ExpressionApp could be done to avoid depending on VTubeStudio's one.