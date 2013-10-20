import time
import logging

import serial
from SWDAdapterBase import *


CMD_WRITE_TMS = ord('8')  # +1
CMD_WRITE_TCK = ord(' ')  # +1 aka SWCLK
CMD_READ_TMS = ord('d')   # aka SWDIO
RESP_ACK = ord('+')
RESP_NACK = ord('-')
RESP_VAL = ord('0')


class Adapter(SWDAdapterBase):

    def __init__(self, options):
        SWDAdapterBase.__init__(self)
        if not options.port:
            raise SWDInitError("Port parameter is required")
        self.hwlog = logging.getLogger("hwcomm")
        self.port = serial.Serial(port=options.port, baudrate=115200, timeout=0.1)
        self.init_adapter()
        self.JTAG2SWD()

    def init_adapter(self):
        pass

    def cmd(self, cmd):
        self.port.write(bytearray([cmd]))
        resp = self.port.read(1)
        print "%02x:%s" % (cmd, resp),
        return ord(resp)

    def readBits(self, num):
        "Read 1-8 bits from SWD"
        res = 0
        mask = 1
        for i in xrange(num):
            self.cmd(CMD_WRITE_TCK | 1)
            self.cmd(CMD_WRITE_TCK)
            v = self.cmd(CMD_READ_TMS)
            if v & 1:
                res |= mask
            mask <<= 1
        print
        self.hwlog.debug("Read %#02x", res)
        return res

    def writeBits(self, val, num):
        "Write 1-8 bits to SWD"
        v = val
        for i in xrange(num):
            self.cmd(CMD_WRITE_TCK | 1)
            self.cmd(CMD_WRITE_TMS + 1 if val & 1 else CMD_WRITE_TMS)
            self.cmd(CMD_WRITE_TCK)
            val >>= 1

        print
        self.hwlog.debug("Wrote %#02x", v)
