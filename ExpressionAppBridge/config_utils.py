import json, os, asyncio

CONFIG_FILEPATH = "config\config.json"

# Some debug flags
debug_settings = {
    "debug_ifm": False,
    "debug_param": [],
    "debug_expapp": False
}

def saveConfig(config):
    ''' Save config file '''
    
    with open(CONFIG_FILEPATH, "w") as f:
        json.dump(config, f)

def loadConfig():
    ''' Load config file. Return empty if missing'''
    
    # Load file
    try:
        with open(CONFIG_FILEPATH) as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    except json.decoder.JSONDecodeError:
        os.remove(CONFIG_FILEPATH)
        config = {}
    
    return config