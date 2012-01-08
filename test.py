#!/usr/bin/python

import NUC1XX
import PirateSWD
import SWDCommon
import sys


def readWholeFile(filename):
    flashfile = open(filename, 'rb')
    return flashfile.read()

if __name__ == '__main__':
    filename = sys.argv[1]
    flash_data = readWholeFile(filename)
    pirate = PirateSWD.PirateSWD('/dev/ttyUSB0', vreg=True)
    debugport = SWDCommon.DebugPort(pirate)
    nuc1xx = NUC1XX.NUC1XX(debugport)
    nuc1xx.halt()
    nuc1xx.changeBS()
    nuc1xx.reset()
    nuc1xx.registerUnlock()
    nuc1xx.enableISP()
    nuc1xx.writeBinToFlash(flash_data)
    print 'config0 register: %x' % nuc1xx.readConfig()
    nuc1xx.changeCBS()
    print 'config0 register: %x' % nuc1xx.readConfig()

    #nuc1xx.eraseFlash()
    #nuc1xx.readFlash(0x00000000)
    #nuc1xx.writeFlash(0x00000000, 0xdeadbeef)
    #nuc1xx.readFlash(0x00100000, len(flash_data))
    #nuc1xx.readFlash(0x00000000)

# vim: set tabstop=4 softtabstop=4 shiftwidth=4 textwidth=80 smarttab expandtab:
