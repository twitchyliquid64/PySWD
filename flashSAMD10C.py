import time
import sys
import struct

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

SAMD_NVM_BASE = 0x41004000
SAMD_NVM_CTRLA_OFFSET = 0x0
SAMD_NVM_CTRLB_OFFSET = 0x4
SAMD_NVM_PARAM_OFFSET = 0x8
SAMD_NVM_INTFLAG_OFFSET = 0x14
SAMD_NVM_STATUS_OFFSET = 0x18
SAMD_NVM_ADDR_OFFSET = 0x1C

NVM_CMDEX_KEY = 0xA5
NVM_CMD_ERASE_ROW = 0x02
NVM_CMD_WRITE_PAGE = 0x04
NVM_CMD_PAGEBUFF_CLEAR = 0x44

FLASH_BASE = 0x0

SAMD10_DEVICES = {
    0x7: {
        "name": "SAMD10C13A",
        "flash": 1024 * 8,
        "ram": 1024 * 4,
    }
}


def loadFile(path):
    with open(path, 'rb') as f:
        d = f.read(8192)
        return [ord(x) for x in d]

def packInt(b1, b2, b3, b4):
    return struct.pack('<L', bytearray([b1,b2,b3,b4]))

class SAMD10C(object):
    def __init__ (self, debugPort):
        self.ahb = MEM_AP(debugPort, 0)
        self.pageSize = self.nvmPageSize()

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

    def nvmPageSize(self):
        pageSize = (self.ahb.readWord(SAMD_NVM_BASE + SAMD_NVM_PARAM_OFFSET) >> 16) & 7
        return {
            0x0: 8,
            0x1: 16,
            0x2: 32,
            0x3: 64,
            0x4: 128,
            0x5: 256,
            0x6: 512,
            0x7: 1024,
        }[pageSize]

    def nvmBusy(self):
        status = self.ahb.readWord(SAMD_NVM_BASE + SAMD_NVM_INTFLAG_OFFSET)
        if bool(status & 2):
            raise Exception("NVM error!")
        return not bool(status & 1)

    def chipErase(self):
        self.ahb.writeWord(SAMD_PAC1_BASE, 1 << 1) # Enable access to the DSU.

        if self.checkDSUErr():
            raise Exception("DSU is in an error state")
        self.ahb.writeByte(SAMD_DSU_BASE + SAMD_DSU_CTRL_OFFSET_EXT, 1 << 4) # CTRL.CE = 1 (start chip-erase)
        time.sleep(1)
        if self.checkDSUErr():
            raise Exception("Chip-erase failed")
        print self.statusa()

    def eraseRow(self, address):
        self.ahb.writeWord(SAMD_NVM_BASE + SAMD_NVM_ADDR_OFFSET, address >> 1)
        self.ahb.writeHalfs(SAMD_NVM_BASE + SAMD_NVM_CTRLA_OFFSET, [(NVM_CMDEX_KEY << 8) + NVM_CMD_ERASE_ROW])
        while self.nvmBusy():
            time.sleep(0.1)

    def automaticWriteEnabled(self):
        return not bool(self.ahb.readWord(SAMD_NVM_BASE + SAMD_NVM_CTRLB_OFFSET) & 128)

    def writePage(self, startAddress, data):
        if len(data) != self.pageSize:
            raise Exception("data does not have a length of pageSize")
        for x in xrange(len(data) / 4):
            d = ((data[x*4] << 24) & 0xFF000000) | ((data[(x*4)+1] << 16) & 0x00FF0000) | ((data[(x*4)+2] << 8) & 0x0000FF00) | ((data[(x*4)+3] & 0xFF))
            # print "Writing %4x to %4x" % (d, startAddress + (x * 4))
            self.ahb.writeWord(startAddress + (x * 4), d)
        while self.nvmBusy():
            time.sleep(0.1)

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
    print "NVM page size = %d" % uc.pageSize
    print "Automatic NVM writes = %s" % str(uc.automaticWriteEnabled())
    if not uc.automaticWriteEnabled():
        raise Exception("Only automatic writes are supported")
    print "NVM busy = %s" % str(uc.nvmBusy())

    print ""
    bin_data = loadFile(sys.argv[1])
    required_pages = len(bin_data) / uc.pageSize + [1 if (len(bin_data) % uc.pageSize) != 0 else 0][0]
    required_rows = required_pages / (uc.pageSize*4) + [1 if (required_pages % (uc.pageSize*4)) != 0 else 0][0]
    print "Firmware is %d bytes in size, using %d pages (%d rows)" % (len(bin_data), required_pages, required_rows)

    for x in xrange(len(bin_data) / 4):
        print "%04x = %08x (%08x)" % (x*4, uc.ahb.readWord(x*4), (bin_data[(x*4)] << 24) + (bin_data[(x*4)+1] << 16) + (bin_data[(x*4)+2] << 8) + (bin_data[(x*4)+3]))


    for x in xrange(required_rows):
        print "Erasing row %d" % (x+1)
        uc.eraseRow(x * (uc.pageSize*4))

    for x in xrange(required_pages):
        start_offset = x * uc.pageSize
        end_offset = (x+1) * uc.pageSize
        if end_offset <= len(bin_data):
            uc.writePage(FLASH_BASE + start_offset, bin_data[start_offset:end_offset])
        else:
            data = bin_data[start_offset:end_offset]
            while len(data) < uc.pageSize:
                data.append(0xFF)
            uc.writePage(FLASH_BASE + start_offset, data)

    if uc.checkDSUErr():
        print "DSU is reporting an error!"
        print uc.statusa()

if __name__ == "__main__":
    main()
