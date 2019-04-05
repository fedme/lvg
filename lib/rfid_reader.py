#!python3
import signal
import asyncio
import evdev

class RfidReader:
    """Allows the use of multiple RFID readers"""

    devices = []
    codeScannedCallback = None
    buffers = {}
    scancodes = {
        # Scancode: ASCIICode
        0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
        10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
        20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
        30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
        40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
        50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
    }

    def __init__(self, deviceName):
        self.registerDevices(deviceName)

    def getAvailableDevices(self):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        return devices
    
    def getActiveDevices(self):
        return self.devices
    
    def registerDevices(self, deviceName):
        allDevices = self.getAvailableDevices()
        self.devices = [d for d in allDevices if d.name == deviceName]
        for device in self.devices:
            self.buffers[device.phys] = ''
        
    def printAvailableDevices(self):
        for device in self.getAvailableDevices():
            print(device)
    
    def printActiveDevices(self):
        for device in self.devices:
            print(device)

    def start(self, codeScannedCallback):
        self.codeScannedCallback = codeScannedCallback
        for device in self.devices:
            asyncio.ensure_future(self.listenToDeviceEvents(device))
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, RfidReader.askExit)
        loop.run_forever()
        loop.close()
    
    @asyncio.coroutine
    async def listenToDeviceEvents(self, device):        
        try:
            async for event in device.async_read_loop():
                if event.type == evdev.ecodes.EV_KEY:
                    e = evdev.categorize(event)
                    if e.keystate == 1:
                        keyval = self.scancodes.get(e.scancode) or ''
                        if keyval == 'CRLF':
                            #print(self.buffers)
                            if self.codeScannedCallback != None:
                                self.codeScannedCallback(device.phys, self.buffers[device.phys])
                            self.buffers[device.phys] = ''
                        else:
                            self.buffers[device.phys] += keyval
        except asyncio.CancelledError:
            raise
    
    @staticmethod
    @asyncio.coroutine
    def exitCoro():
        loop = asyncio.get_event_loop()
        loop.stop()

    @staticmethod
    def askExit():
        for task in asyncio.Task.all_tasks():
            task.cancel()
        asyncio.async(RfidReader.exitCoro())
