#!/usr/bin/python

import serial
import PirateSWD
import SWDCommon
import NUC1XX
import time

if __name__ == '__main__':
  pirate = PirateSWD.PirateSWD('/dev/ttyUSB0')
  debugport = SWDCommon.DebugPort(pirate)
  nuc1xx = NUC1XX.NUC1XX(debugport)
  nuc1xx.halt()
  #nuc1xx.readAllRom()
  #nuc1xx.readConfig()
  nuc1xx.flashUnlock()
  nuc1xx.eraseFlash()
  nuc1xx.writeFlash(0x00100000, 0xdeadbeef)
  nuc1xx.readFlash(0x00100000)
