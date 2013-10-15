import time
import logging

import serial
from SWDAdapterBase import *


CMD_HANDSHAKE = "?SWD?"
CMD_HANDSHAKE_REPLY = "!SWD1"
CMD_WRITE_WORD = 0x90
CMD_WRITE_BITS = 0xa0
CMD_WRITE_BYTE = CMD_WRITE_BITS | (8 - 1)
CMD_READ_WORD = 0x10
CMD_READ_BITS = 0x20
CMD_CYCLE_CLOCK = 0x28


class mchck_swd(SWDAdapterBase):

    def __init__(self, options):
        SWDAdapterBase.__init__(self)
        if not options.port:
            raise SWDInitError("Port parameter is required")
        self.hwlog = logging.getLogger("hwcomm")
        self.port = serial.Serial(port=options.port, baudrate=115200, timeout=0.1)
        self.init_adapter()
        self.JTAG2SWD()

    def init_adapter(self):
        for i in xrange(20):
            self.port.write(CMD_HANDSHAKE)
            reply = self.port.read(len(CMD_HANDSHAKE_REPLY))
            if reply == CMD_HANDSHAKE_REPLY:
                return True
            time.sleep(0.1)
        raise SWDInitError("Did not get handshake reply")

    def readBits(self, num):
        "Read 1-8 bits from SWD"
        v = bytearray([CMD_READ_BITS | (num - 1)])
        self.port.write(v)
        self.hwlog.debug("Wrote %s", self.renderHex(v))
        v = ord(self.port.read(1))
        self.hwlog.debug("Read %#02x", v)
        return v

    def writeBits(self, val, num):
        "Write 1-8 bits to SWD"
        v = bytearray([CMD_WRITE_BITS | (num - 1), val])
        self.hwlog.debug("Wrote %s", self.renderHex(v))
        self.port.write(v)

    @staticmethod
    def renderHex(arr):
        return " ".join([hex(x) for x in arr])
