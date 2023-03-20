import asyncio, signal, functools, json, argparse
from ExpressionAppBridge.ExpressionApp import start_ExpressionApp
from ExpressionAppBridge.iFM import iFM_Data, start_iFM_Sender
from ExpressionAppBridge.tracking_data import TrackingData
from ExpressionAppBridge.ExpToPerfSync import ExpToPerfSync
from ExpressionAppBridge.config_utils import loadConfig, config_file_refresher, debug_settings

def sig_handler(stop_event, signum, frame):
    stop_event.set()

async def main(args):
    # Load and validate config
    config = loadConfig('ExpressionAppBridge\config.json')
    
    # Set up tracking storage
    tdata = TrackingData()
    
    # Set up iFM serializer
    iFM = iFM_Data(tdata)
    
    # Set up parser
    parser = ExpToPerfSync(config, tdata, disable_head_pos=True)
    
    await asyncio.gather(start_ExpressionApp(config, parser.parseExpressionAppMessage, args.cal), start_iFM_Sender(config['iFM']['addr'], config['iFM']['port'], iFM), config_file_refresher('ExpressionAppBridge\config.json', config))



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
    
    with asyncio.Runner() as runner:
        try:
            runner.run(main(args))
        except KeyboardInterrupt:
            pass
        runner.run(asyncio.sleep(0.5))