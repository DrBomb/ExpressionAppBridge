import asyncio, signal, functools, json, argparse
from ExpressionAppBridge.ExpressionApp import start_ExpressionApp, setup
from ExpressionAppBridge.iFM import iFM_Data, start_iFM_Sender
from ExpressionAppBridge.tracking_data import TrackingData
from ExpressionAppBridge.ExpToPerfSync import ExpToPerfSync
from ExpressionAppBridge.config_utils import loadConfig, debug_settings

async def main(args, config, camera_conf):
    # Set up tracking storage
    tdata = TrackingData()
    
    # Set up iFM serializer
    iFM = iFM_Data(tdata)
    
    # Set up parser
    parser = ExpToPerfSync(tdata)
    
    async with asyncio.TaskGroup() as tg:
        # Start blendshape config file watcher
        watcher_task = tg.create_task(parser.start_config_watcher())
        
        # Start ExpressionApp
        ExpresssionApp_task = tg.create_task(start_ExpressionApp(config, camera_conf, parser.parseExpressionAppMessage, args.cal))
        
        # Start iFM sender
        iFM_Sender_task = tg.create_task(start_iFM_Sender(iFM))



if __name__ == "__main__":
    # Command line stuff
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-ifm', help="Print every iFM frame sent. VERY VERBOSE", action='store_true')
    parser.add_argument('--debug-expapp', help="Print ExpressionApp console output", action='store_true')
    parser.add_argument('--debug-param', help="Provide a comma separated list of parameters to be printed when iFM is set partial matches are allowed. IE. 'brow,blink'", action='store', metavar='param')
    parser.add_argument('--cal', action='store_true', help="Do a calibration on start")
    
    # Parse command line args
    args = parser.parse_args()
    
    # Load command line args to debug struct
    debug_settings['debug_ifm'] = args.debug_ifm
    debug_settings['debug_param'] = args.debug_param.split(',') if args.debug_param is not None else []
    debug_settings['debug_expapp'] = args.debug_expapp
    
    # Load config file.
    config = loadConfig()
    
    # Test the ExpressionApp path, ask for camera settings
    camera_conf = setup(config)
    
    with asyncio.Runner() as runner:
        try:
            runner.run(main(args, config, camera_conf))
        except KeyboardInterrupt:
            pass
        runner.run(asyncio.sleep(0.5))