import unittest, json, os
from tempfile import NamedTemporaryFile
from ExpressionAppBridge import cal
from ExpressionAppBridge.tracking_data import TrackingData

class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.td = TrackingData()
    def test_nofile(self):
        ''' Test non existent file '''
        
        # Create temp file, delete it right away and save its route
        tempfile = NamedTemporaryFile(delete=False)
        tempfile.close()
        os.remove(tempfile.name)
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Expected output
        exp_config = {
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
        
        # Compare output
        self.assertEqual(exp_config, instance.config)
        
        # When the file is missing, it gets created
        with open(tempfile.name) as f:
            tempfilecontents = json.load(f)
        
        # Compare contents
        self.assertEqual(exp_config, tempfilecontents)
        
        # Finally delete tempfile
        os.remove(tempfile.name)
    
    def test_invalid_json(self):
        ''' Test json parse failure with an empty file '''
        
        # Create temp file, close and save its route
        tempfile = NamedTemporaryFile(delete=False)
        tempfile.close()
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Expected output
        exp_config = {
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
        
        # Compare output
        self.assertEqual(exp_config, instance.config)
        
        # When the file is missing, it gets created
        with open(tempfile.name) as f:
            tempfilecontents = json.load(f)
        
        # Compare contents
        self.assertEqual(exp_config, tempfilecontents)
        
        # Finally delete tempfile
        os.remove(tempfile.name)
    
    def test_invalid_eyes(self):
        ''' Test invalid eyes setup. It should not touch the other callibration members! '''
        
        # Input and expected output
        cal_in = {
            "eyes": {
                "left": {
                    "fullScale": 80
                },
                "right": {
                    "maxRotation": 30
                }
            },
            "blendshapes": {
                "eyeBlink_L": {
                  "type": "outputSnap",
                  "limit": 60
                }
            }
        }
        cal_out = {
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
                }
            }
        }
        
        # Create temp file, fill it with input and close it
        tempfile = NamedTemporaryFile(delete=False, mode='w')
        json.dump(cal_in, tempfile)
        tempfile.close()
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Check config result
        self.assertEqual(instance.config, cal_out)
        
        # Finally delete tempfile
        os.remove(tempfile.name)
    
    def test_eye_missing(self):
        ''' Test eyes missing in config file '''
        
        # Input and expected output
        cal_in = {
            "blendshapes": {
                "eyeBlink_L": {
                  "type": "outputSnap",
                  "limit": 60
                }
            }
        }
        cal_out = {
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
                }
            }
        }
        
        # Create temp file, fill it with input and close it
        tempfile = NamedTemporaryFile(delete=False, mode='w')
        json.dump(cal_in, tempfile)
        tempfile.close()
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Check config result
        self.assertEqual(instance.config, cal_out)
        
        # Finally delete tempfile
        os.remove(tempfile.name)
    
    def test_all_valid_interpolations(self):
        ''' Test that this config passes completely '''
        
        cal_in = {
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
                "browDown_L": {
                  "type": "interpolation",
                  "minIn": 0,
                  "maxIn": 50,
                  "minOut": 0,
                  "maxOut": 100
                },
                "browDown_R": {
                  "type": "simple",
                  "max": 50
                },
            }
        }
        
        # Create temp file, fill it with input and close it
        tempfile = NamedTemporaryFile(delete=False, mode='w')
        json.dump(cal_in, tempfile)
        tempfile.close()
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Check config result
        self.assertEqual(instance.config, cal_in)
        
        # Finally delete tempfile
        os.remove(tempfile.name)
    
    def test_strip_invalid_entries(self):
        ''' Cal entries with missing parameters should be removed from the config object '''
        
        cal_in = {
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
                  "limit": 60
                },
                "eyeBlink_R": {
                  "type": "outputSnap"
                },
                "eyeWide_L": {
                  "type": "normal",
                  "limit": 60
                },
                "browDown_L": {
                  "type": "interpolation",
                  "minIn": 0,
                  "maxIn": 50,
                  "minOut": 0
                },
                "browDown_R": {
                  "type": "interpolation",
                  "minIn": 0,
                  "maxIn": 50,
                  "maxOut": 100
                },
                "browOuterUp_L": {
                  "type": "interpolation",
                  "minIn": 0,
                  "minOut": 0,
                  "maxOut": 100
                },
                "browOuterUp_R": {
                  "type": "interpolation",
                  "maxIn": 50,
                  "minOut": 0,
                  "maxOut": 100
                },
                "browInnerUp": {
                  "type": "simple"
                },
                "mouthLeft": {
                    "type": "outputSnap",
                    "limit": 60
                }
            }
        }
        
        cal_out = {
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
                "mouthLeft": {
                    "type": "outputSnap",
                    "limit": 60
                }
            }
        }
        
        # Create temp file, fill it with input and close it
        tempfile = NamedTemporaryFile(delete=False, mode='w')
        json.dump(cal_in, tempfile)
        tempfile.close()
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Check config result
        self.assertEqual(instance.config, cal_out)
        
        # Finally delete tempfile
        os.remove(tempfile.name)
    
    def test_strip_not_found_blendshape(self):
        ''' Remove blendshape settings that are not on the PS list '''
        
        cal_in = {
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
                "InvalidBlendshape": {
                  "type": "outputSnap",
                  "limit": 60
                },
                "browDown_L": {
                  "type": "interpolation",
                  "minIn": 0,
                  "maxIn": 50,
                  "minOut": 0,
                  "maxOut": 100
                },
                "browDown_R": {
                  "type": "simple",
                  "max": 50
                },
            }
        }
        
        cal_out = {
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
                "browDown_L": {
                  "type": "interpolation",
                  "minIn": 0,
                  "maxIn": 50,
                  "minOut": 0,
                  "maxOut": 100
                },
                "browDown_R": {
                  "type": "simple",
                  "max": 50
                },
            }
        }
        
        # Create temp file, fill it with input and close it
        tempfile = NamedTemporaryFile(delete=False, mode='w')
        json.dump(cal_in, tempfile)
        tempfile.close()
        
        # Create new instance
        instance = cal.TrackingInput(self.td, tempfile.name)
        
        # Check config result
        self.assertEqual(instance.config, cal_out)
        
        # Finally delete tempfile
        os.remove(tempfile.name)