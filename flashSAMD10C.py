import time
import sys
import array

from PirateSWD import *
from SWDCommon import *

SAMD_DSU_BASE = 0x41002000
SAMD_DSU_DID_OFFSET = 0x18
SAMD_DSU_CTRL_OFFSET_EXT = 0x100
SAMD_DSU_STATUSA_OFFSET = 0x1
SAMD_DSU_STATUSB_OFFSET = 0x2

SAMD_PORT_BASE = 0x41004400
SAMD_PORT_DIRSET_OFFSET = 0x08
SAMD_PORT_OUT_OFFSET = 0x10

SAMD_PAC1_BASE = 0x41000000

SAMD10_DEVICES = {
    0x7: {
        "name": "SAMD10C13A",
        "flash": 1024 * 8,
        "ram": 1024 * 4,
    }
}

class SAMD10C(object):
    def __init__ (self, debugPort):
        self.ahb = MEM_AP(debugPort, 0)

    def deviceID(self):
        return self.ahb.readWord(SAMD_DSU_BASE + SAMD_DSU_DID_OFFSET)

    def device(self):
        devsel = self.deviceInfo()["devsel"]
        if devsel in SAMD10_DEVICES:
            return SAMD10_DEVICES[devsel]

    def deviceInfo(self):
        did = self.deviceID()
        return {
            "processor": did >> 28,
            "family": ((did >> 23) & 0x1F),
            "series": ((did >> 16) & 0x3F),
            "devsel": (did & 0xFF),
        }

    def statusa(self):
        return self.ahb.readByte(SAMD_DSU_BASE + SAMD_DSU_STATUSA_OFFSET)

    def protected(self):
        return bool(self.ahb.readWord(SAMD_DSU_BASE + SAMD_DSU_STATUSB_OFFSET) & 0x1)

    def checkDSUErr(self):
        statusa = self.statusa()
        # Bits: 2 = bus-err, 3 = DSU failure, 4 = protection err
        return bool(statusa & 4) or bool(statusa & 8) or bool(statusa & 16)

    def chipErase(self):
        self.ahb.writeWord(SAMD_PAC1_BASE, 1 << 1) # Enable access to the DSU.

        if self.checkDSUErr():
            raise Exception("DSU is in an error state")
        self.ahb.writeByte(SAMD_DSU_BASE + SAMD_DSU_CTRL_OFFSET_EXT, 1 << 4) # CTRL.CE = 1 (start chip-erase)
        time.sleep(1)
        if self.checkDSUErr():
            raise Exception("Chip-erase failed")
        print self.statusa()


    def setGPIO(self, paPin):
        self.ahb.writeWord(SAMD_PORT_BASE + SAMD_PORT_DIRSET_OFFSET, 1 << paPin)
        self.ahb.writeWord(SAMD_PORT_BASE + SAMD_PORT_OUT_OFFSET, 1 << paPin)

def main():
    # V-regs = on
    # RED --> 3.3V
    # WHITE --> SWDIO
    # PURPLE --> SWDCLK
    # BROWN --> GND
    busPirate = PirateSWD("/dev/ttyUSB0", True, 2)
    debugPort = DebugPort(busPirate)
    uc = SAMD10C(debugPort)

    dev = uc.device()
    if dev:
        print "Detected %s" % dev["name"]
    else:
        print uc.deviceInfo()
    print "protected = %s" % uc.protected()

    if uc.checkDSUErr():
        print "DSU is reporting an error!"
        print uc.statusa()

    #uc.chipErase()
    uc.setGPIO(24)

if __name__ == "__main__":
    main()
