# ExpressionAppBridge

## Purpose

This program uses VTube Studio's RTX tracking to provide tracking to VSeeFace via the iFacialMocap protocol

## Features

 * Opens and closes RTX tracking without opening VTube Studio
 * Outputs all ARTracking blendshapes sans "tongueOut" with varying levels of accuracy
 * Rotation and position tracking
 * Stops sending tracking data when confidence value is low
 * Blendshape calibration via config file
 * Internal averaging for position and rotation values
 
## Requirements

The only thing required to run this program is Python 3.11.

Download it from the official website and make sure it is installed to your PATH

## Usage

To run the program, navigate to the ExpressionAppBridge folder and run the main file. `python main.py`. Then go to VSeeFace, disable face tracking if you have it enabled and enable "ARKit Tracking Receiver" with "iFacialMocap" as the tracking app.

To exit, press CTRL + C on the Command Prompt window

On that same folder you will find the config file `config.json` and the calibration file `ExpApp_Cal.json` if a calibration had been done before

### Command line parameters

There are a few flags you can pass before starting the software

 * `--debug-ifm` will print the iFM frame
 * `--debug-expapp` will enable ExpressionApp printing to console
 * `--debug-param params` params should be a comma separated list of terms, those parameters will get printed to console. It needs some work.
 * `--cal` will force a calibration call regardless if the cal file is present

### Calibration

The calibration file is stored in `ExpApp_Cal.json`. If the file is missing, the program will wait 10 seconds and will trigger a calibration on the RTX tracking app. The resulting calibration will be stored on the file to be passed next time the program is started. Use the `--cal` flag to calibrate on every startup.

### Config file

The config file is stored in `config.json`. It has a few fields. Here's a rough reference. There is also a .sample file for you to use in case it is lost.

```
{
    "camera": 0,     // Camera number. Starts from 0
    "ifm": {         // iFM sender settings. In case you need to send it somewhere else. It will default to these values
        "addr": "127.0.0.1",
        "port": 49983
    },
    "expapp_dir": "", // REQUIRED. ExpressionApp directory location. It should be inside your VTubeStudio dir at "VTube Studio_Data\StreamingAssets\MXTracker"
    "calibration": {  
        "eyes": {     // Eyes calibration. Full scale is the max input and maxRotation is the max deflection for both left and right eyes
            "left": {
                "maxRotation": 80,
                "fullScale": 80
            },
            "right": {
                "maxRotation": 80,
                "fullScale": 80
            }
        },
        "blendshapes": {   // Blendshape calibrations for better expressions
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
}

```

#### Blendshape configs

Each ARKit blendshape can be interpolated between multiple modes. The input will be the blendshape input received from the ExpressionApp, and the output is the value sent to VTubeStudio

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

## Possible Future plans

Depends on how well or not this program runs, some are good to have but not critical.

 * Make the program easier to distribute with pyinstaller or something else
 * Use YAML instead of JSON for config
 * Implement an UI with buttons for calibrate and hide/show features window
 * Fork our own ExpressionApp to avoid using VTubeStudio's one
 * Stop using python and port to C++

## Support

You can follow me on my personal twitter [@Dr_Bomb](https://twitter.com/Dr_Bomb) and you can also follow my VTuber twitter account [TsukinoYueVT](https://twitter.com/TsukinoYueVT) as I plan to start streaming too!

I do not possess a perfect sync avatar, so my streams might not even benefit from this program just yet lol. You can also DM me if you wanna donate something.

