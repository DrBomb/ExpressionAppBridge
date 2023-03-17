'''
iFM.py

iFacialMocap layer.

iFM_Data is a class that can serialize a tracking_data object.

start_iFM_Sender is a asyncio coroutine that will send the data at FREQ frequency
'''

import asyncio
from config_utils import debug_settings
FREQ = 60

class iFM_Data:
    def __init__(self, tracking_data):
        self.tracking_data = tracking_data
        self.head_enable = True
        self.rightEye_enable = True
        self.leftEye_enable = True
    def __str__(self):
        """Serialize tracking_data according to the iFaceMocap format"""
        
        # Serialize blendshapes
        output = "|".join([f"{k}-{int(v)}" for k, v in self.tracking_data.blendshapes.items()])
        # Head parameters
        output = output + "|=head#" + ",".join(["{:.6f}".format(x) for x in self.tracking_data.head])
        # Right Eye
        if self.rightEye_enable:
            output = output + "|rightEye#" + ",".join(["{:.6f}".format(x) for x in self.tracking_data.rightEye])
        # Left Eye
        if self.leftEye_enable:
            output = output + "|leftEye#" + ",".join(["{:.6f}".format(x) for x in self.tracking_data.leftEye])
        # Closing
        output = output + "|"
        return output

class IFM_Sender_Protocol:
    def __init__(self):
        self.transport = None
    def connection_made(self, transport):
        self.transport = transport
    def connection_lost(self, exp):
        # Ignore lost connections
        pass
    def error_received(self, exp):
        # Ignore unreachable destinations
        pass

async def start_iFM_Sender(addr, port, iFM):
    """Start iFM sender. Rate is set to FREQ"""
    print("Setting up iFM sender", flush=True)
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: IFM_Sender_Protocol(),
        remote_addr=(addr, port))
    try:
        while True:
            # Send data if tracking_data.confidence is greater than 25
            if iFM.tracking_data.confidence > 25:
                payload = str(iFM)
                if debug_settings['debug_ifm']:
                    print(payload)
                transport.sendto(payload.encode())
            await asyncio.sleep(1/FREQ)
    except asyncio.CancelledError:
        pass
    finally:
        print("Stopping iFM sender", flush=True)
        transport.close()