#!/usr/bin/python

import time
import sys
import array

from PirateSWD import *
from SWDCommon import *
from EFM32 import *

def loadFile(path):
    arr = array.array('I')
    try:
        arr.fromfile(open(sys.argv[1], 'rb'), 1024*1024)
    except EOFError:
        pass
    return arr.tolist()

def main():
    busPirate = PirateSWD("/dev/tty.usbserial-buspirat", vreg = True)
    debugPort = DebugPort(busPirate)
    efm32     = EFM32(debugPort)

    #print "DP.IDCODE: %08X" % debugPort.idcode()
    #print "AP.IDCODE: %08X" % efm32.ahb.idcode()
    #print ""
    part_info = efm32.ahb.readWord(0x0FE081FC) # PART_NUMBER, PART_FAMILY, PROD_REV
    mem_info = efm32.ahb.readWord(0x0FE081F8)  # MEM_INFO_FLASH, MEM_INFO_RAM
    flash_size = mem_info & 0xFFFF
    if (part_info >> 16 & 0xFF) == 71:
        print "Connected."
        print "Part number: EFM32G%dF%d (production ID = %d)" % (part_info & 0xFF, 
                flash_size, part_info >> 24 & 0xFF)
    else:
        print "Warning: unknown part"
        sys.exit()
    print "Loading File: '%s'..." % sys.argv[1],
    vals = loadFile(sys.argv[1])
    size = len(vals) * 4
    print "loaded %d bytes." % size
    if size / 1024.0 > flash_size:
        print "Firmware will not fit into flash!"
        sys.exit(1)

    efm32.halt()
    print "Erasing Flash"
    efm32.flashUnlock()
    efm32.flashErase(flash_size)
    print "Programming Flash"
    efm32.flashProgram()
    efm32.flashWrite(vals)
    efm32.flashProgramEnd()
    print "Resetting"
    efm32.sysReset()

if __name__ == "__main__":
    main()
