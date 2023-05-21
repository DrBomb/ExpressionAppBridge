# ExpressionAppBridge

## Purpose

This program can provide iFacialMocap tracking data using either VTube Studio's RTX tracking or Google's mediapipe framework for use on VTubing applications such as VSeeFace or VNyan.

## Features

 * Supports opening and closing the RTX Tracking package that comes bundled with VTube Studio RTX Tracking DLC
 * Supports Google's mediapipe facial landmark detection
 * Outputs iFacialMocap data to localhost at 49983 port
 * Rotation and position tracking
 * Blendshape calibration for both tracking modes on separate files
 * Internal averaging for position and rotation values

## Installation

Download the .zip file on the [releases](https://github.com/DrBomb/ExpressionAppBridge/releases) page and extract it somehere

## Running/Building from source

The latest Python version supported by mediapipe is 3.10.

 * Clone the repo
 * Create a new virtualenv for your project
 * Install the dependencies
  * `pip install mediapipe==0.10.0 transforms3d pyinstaller pygrabber`
 * Download the Face Landmark model file from [this page](https://developers.google.com/mediapipe/solutions/vision/face_landmarker#models)
 * Make sure the model file is called `face_landmarker.task` and on the same folder as `main.py`
 * Run the program with `python main.py`
 * Build the distribution package with `pyinstaller main.py --add-data config;config`
 * Copy `face_landmarker.task` to dist/main before compressing.

## Usage

Run the program `main.exe` to start. This is a console program, so a console window will be opened if ran from desktop.

 * After running it will ask which mode to use. RTX Tracking or mediapipe tracking.
 * RTX Tracking will first ask for the path of the VTube Studio RTX tracking DLC. Make sure `ExpressionApp.exe` is present on this path.
  * Then you will be prompted for camera and capture format.
  * Next thing, the ExpressionApp will run and you will see a face with the tracking effects.
 * With mediapipe tracking, you will be prompted for camera and capture format.
  * Afterwards, an FPS counter will be shown.
 * Close either tracker by pressing Ctrl + C on the console

## VSeeFace setup

Refer to VSeeFace's [documentation](https://www.vseeface.icu/#iphone-face-tracking) on the iPhone section. The phone IP should be set to `127.0.0.1` which is the loopback address and the format should be `iFacialMocap`. Make sure to check the features you want received!

## RTX Tracking

 * 51 blendshape detection. tongueOut not supported at all.
  * puffCheeks listed as supported but not really detected
 * Requires an RTX series Nvidia GPU
 * Seems to be based NVidia's sample applications
 * Adapted by VTube Studio
 * There is a calibration procedure that will happen on first boot after 5 seconds
  * The calibration is done by the program. The results are stored in `config/RTX_internal_cal.json` and passed on start
  * You can force a new calibration by passing the `--cal` flag to the program or by deleting the file

## Mediapipe Tracking

 * 51 blendshape detection. tongueOut not supported.
  * puffCheeks does not seem to be detectable as well
 * No idea if it requires a GPU, it seems to use it anyways.
 * Runs at ~32 FPS on my computer. No idea if it is due to my webcam or python slowdown.
 * Model and task development seems to be on the experimental stage.
 * Seems to be overly sensitive to mouthFunnel for some reason. Could be training bias as I am not from the USA.

### Command line parameters

There are a few flags you can pass before starting the software

 * `--debug-ifm` will print the iFM frame to console
 * `--debug-expapp` will enable ExpressionApp (RTX Tracking) printing to console
 * `--cal` will force an RTX tracking calibration 5 seconds after starting tracking

### Blendshape Config

Blendshape values for both modes sometimes are not good enough to give a good VTubing impression, so there is a blendshape calibration system that provides ways to adjust the values that get sent to VSeeFace.

Each mode has its own config file, `config\RTX_Blendshapes_cal.json` for RTX tracking, `Mediapipe_Blendshapes_cal.json` for Mediapipe tracking.

Here's the default contents:

```
{
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
  "blendshapes": {
    "eyeBlink_L": {
      "type": "outputSnap",
      "limit": 60
    },
    "eyeBlink_R": {
      "type": "outputSnap",
      "limit": 60
    },
    "browDown_L": {
      "type": "simple",
      "max": 50
    },
    "browDown_R": {
      "type": "simple",
      "max": 50
    },
    "mouthLeft": {
      "type": "simple",
      "max": 50
    },
    "mouthRight": {
      "type": "simple",
      "max": 50
    }
  }
}
```

#### Blendshape configs

Each ARKit blendshape can be interpolated between multiple modes. The input will be the blendshape input received from tracking, and the output is the value sent to VSeeFace via iFm

On the blendshape config, the key corresponds to the ARKit blendshape input. Inside the object, you will need to specify the kind of interpolation you want on that blendshape, with the type there are some required parameters the object will need to have in order to apply the interpolation. The program will ignore and print out if there are malformed interpolation entries.

Blendshape configs will be reloaded on runtime so you can adjust them while checking their effects.

##### Simple interpolation

Simple has a `max` argument. That means that when the input is at `max` the output blendshape will be 100. For example. With a max value of 50, if the input is 25, the output is 50. Output will not be higher than 100. Useful for increasing sensitivity on blendshapes that might not be as responsive as you'd like.

Example:
```
"mouthRight": {
    "type": "simple",
    "max": 50
}
```

##### Output Snap interpolation

Output snap has a `limit` argument. When the input exceeds this limit, the output is instantly snapped to 100. No interpolation in between. This might be useful to make sure your eyes close when needed, as the input might not reach 100 and your eyes might not close completely

Example:
```
"eyeBlink_R": {
    "type": "outputSnap",
    "limit": 60
}
```

##### "interpolation" type

This is the most thorough type of interpolation, you have 4 parameters. `minIn`, `maxIn`, `minOut` and `maxOut`. As they imply, `minIn` and `maxIn` specify the input ranges of the operation, the inputs will be snapped to those values as well. `minOut` and `maxOut` represent the output range. This means a `min` range will be mapped out to a `max` range with approximately the same ratio. Useful when you want an interpolation type but the output also needs to have a minimum output.

Example:

```
"mouthRight": {
    "type": "interpolation",
    "minIn": 0,
    "maxIn": 50,
    "minOut": 0,
    "maxOut": 100
}
```

This example with minIn and minOut being 0 is pretty much the same as selecting a simple interpolation type.

## Disclaimers

These tracking softwares and AI models were not developed by me. I am just making them available via the iFM protocol to be used by other programs. As such, I won't be able to help too much in regards to quality of tracking or issues resulting from training biases. Feel free to contact me though, thanks for taking a look at my work.

## Support

You can follow me on my personal twitter [@Dr_Bomb](https://twitter.com/Dr_Bomb) and you can also follow my VTuber twitter account [TsukinoYueVT](https://twitter.com/TsukinoYueVT) as I plan to start streaming too!

I do not possess a perfect sync avatar, so my streams might not even benefit from this program just yet! But I appreciate any feedback you can give me.

## Contact

You can write to me at my twitter handles. I also lurk a lot on Deat's discord on the VSeeFace channel. You can check on the VSeeFace website and find the discord link there. I am also present on Suvidriel's discord.

