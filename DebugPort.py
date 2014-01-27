from SWDProtocol import *
from SWDErrors import *
# Debug Port registers
# p.6-5
REG_IDCODE = 0 << 3     # Read
REG_ABORT = 0 << 3      # Write
REG_CTRL_STAT = 1 << 3  # Read/Write, CTRLSEL=0
REG_WCR = 1 << 3        # Read/Write, CTRLSEL=1
REG_RESEND = 2 << 3     # Read
REG_SELECT = 2 << 3     # Write
REG_READBUFF = 3 << 3   # Read
REG_ROUTESEL = 3 << 3   # Write, reserved


class DebugPort:

    ID_CODES = (
        0x1BA01477,  # EFM32-cortex-M3
        0x2BA01477,  # STM32
        0x0BB11477,  # NUC1xx
        0x0bc11477,  # EFM32-cortex-M0
        )

    def __init__(self, swd):
        self.swd = swd
        # "After the host has transmitted a line request sequence to the
        # SW-DP, it must read the IDCODE register." p.5-10
        idcode = self.idcode()
        if idcode not in DebugPort.ID_CODES:
            print "warning: unexpected idcode: ", hex(idcode)
        # Clear any sticky errors
        self.abort(orunerr=True, wdataerr=True, stickyerr=True, stickycmp=True)
        # get the SELECT register to a known state
        self.select(0, 0)
        self.curAP = 0
        self.curBank = 0
        # power up DAP
        self.swd.writeCmd(OP_DP, REG_CTRL_STAT, 0x54000000)
        s = self.status()
        if (s >> 24) != 0xF4:
            raise SWDInitError("Error powering up system, status: %#x" % s)

    def idcode(self):
        return self.swd.readCmd(OP_DP, REG_IDCODE)

    def abort(self, orunerr, wdataerr, stickyerr, stickycmp, dap=False):
        value = 0x00000000
        value = value | (0x10 if orunerr else 0x00)
        value = value | (0x08 if wdataerr else 0x00)
        value = value | (0x04 if stickyerr else 0x00)
        value = value | (0x02 if stickycmp else 0x00)
        value = value | (0x01 if dap else 0x00)
        self.swd.writeCmd(OP_DP, REG_ABORT, value)

    def status(self):
        return self.swd.readCmd(OP_DP, REG_CTRL_STAT)

    def control(self, trnCount=0, trnMode=0, maskLane=0, orunDetect=0):
        value = 0x54000000
        value = value | ((trnCount & 0xFFF) << 12)
        value = value | ((maskLane & 0x00F) << 8)
        value = value | ((trnMode  & 0x003) << 2)
        value = value | (0x1 if orunDetect else 0x0)
        self.swd.writeCmd(OP_DP, REG_CTRL_STAT, value)

    def select(self, apsel, apbank):
        value = 0x00000000
        value = value | ((apsel  & 0xFF) << 24)
        value = value | ((apbank & 0x0F) << 4)
        self.swd.writeCmd(OP_DP, REG_SELECT, value)

    def readReadbuff(self):
        return self.swd.readCmd(OP_DP, REG_READBUFF)

    def readAP(self, apsel, address):
        adrBank = (address >> 4) & 0xF
        adrReg  = (address >> 2) & 0x3
        if apsel != self.curAP or adrBank != self.curBank:
            self.select(apsel, adrBank)
            self.curAP = apsel
            self.curBank = adrBank
        return self.swd.readCmd(OP_AP, adrReg)

    def writeAP(self, apsel, address, data, ignore=False):
        adrBank = (address >> 4) & 0xF
        adrReg  = (address >> 2) & 0x3
        if apsel != self.curAP or adrBank != self.curBank:
            self.select(apsel, adrBank)
            self.curAP = apsel
            self.curBank = adrBank
        self.swd.writeCmd(OP_AP, adrReg, data, ignore)
