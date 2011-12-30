#!/usr/bin/python

# SWD adapter for the Nucon NUC1XX series.

# TODO: make it work, flash can't be written directly through ISP as it seems

__author__ = 'Pascal Hahn <ph@lxd.bz>'

import SWDCommon

class NotReadyForCommandException(Exception):
  pass


class NUC1XX(object):
  REGRWPROT_ADDR = 0x50000100
  ISPCON_ADDR = 0x5000C000
  ISPTRG_ADDR = 0x5000C010
  ISPADR_ADDR = 0x5000C004
  ISPDAT_ADDR = 0x5000C008
  ISPCMD_ADDR = 0x5000C00C

  def __init__(self, debugport):
    self.ahb = SWDCommon.MEM_AP(debugport, 0)

  def halt (self):
    # halt the processor core
    self.ahb.writeWord(0xE000EDF0, 0xA05F0003)

  def flashUnlock(self):
    # disable write protection
    self.ahb.writeBlock(NUC1XX.REGRWPROT_ADDR, [0x59])
    self.ahb.writeBlock(NUC1XX.REGRWPROT_ADDR, [0x16])
    self.ahb.writeBlock(NUC1XX.REGRWPROT_ADDR, [0x88])

    # enable ISP
    self.ahb.writeWord(NUC1XX.ISPCON_ADDR, 0x00000001)

  def issueISPCommand(self, adr, cmd, data):
    if self.ahb.readBlock(NUC1XX.ISPTRG_ADDR, 0x01) != [0x00]:
      raise NotReadyForCommandException('not yet ready for command')
    self.ahb.writeWord(NUC1XX.ISPADR_ADDR, adr)
    self.ahb.writeBlock(NUC1XX.ISPCMD_ADDR, [cmd])
    self.ahb.writeWord(NUC1XX.ISPDAT_ADDR, data)

    # trigger command execution
    self.ahb.writeBlock(NUC1XX.ISPTRG_ADDR, [0x01])
    while True:
      # successful execution
      if self.ahb.readBlock(NUC1XX.ISPTRG_ADDR, 0x01) == [0x00]:
        print 'command executed'
        break
      # TODO: for now we assume success, actually verify it

  def writeFlash(self):
    self.issueISPCommand(0x1000, 0x21, 0xDEADBEEF)

  def readFlash(self):
    print str(map(bin, self.ahb.readBlock(0x1000, 0x10)))

  def eraseFlash(self):
    self.issueISPCommand(0x1000, 0x22, 0x00)

