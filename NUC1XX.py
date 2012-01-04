#!/usr/bin/python

# SWD adapter for the Nucon NUC1XX series.

# TODO: make it work, flash can't be written directly through ISP as it seems

__author__ = 'Pascal Hahn <ph@lxd.bz>'

import struct
import SWDCommon

class NotReadyForCommandException(Exception):
  pass


class UnlockFailedException(Exception):
  pass


class NUC1XX(object):
  CONFIG0_ADDR = 0x00300000

  ISPCON_ADDR = 0x5000C000
  ISPADR_ADDR = 0x5000C004
  ISPDAT_ADDR = 0x5000C008
  ISPCMD_ADDR = 0x5000C00C
  ISPTRG_ADDR = 0x5000C010

  IPRSTC_ADDR = 0x50000008

  DHCSR_ADDR = 0xE000EDF0

  DCRSR_ADDR = 0xE000EDF4
  DCRDR_ADDR = 0xE000EDF8

  AIRCR_ADDR = 0xE000ED0C

  REGRWPROT_ADDR = 0x50000100

  def __init__(self, debugport):
    self.ahb = SWDCommon.MEM_AP(debugport, 0)

  def halt (self):
    self.ahb.writeWord(NUC1XX.DHCSR_ADDR, 0xA05F0003)

  def unhalt(self):
    self.ahb.writeWord(NUC1XX.DHCSR_ADDR, 0xA05F0001)

  def step(self):
    self.ahb.writeWord(NUC1XX.DHCSR_ADDR, 0xA05F0005)

  def reset(self):
    self.ahb.writeWord(NUC1XX.IPRSTC_ADDR, 0x01)

  def flashUnlock(self):
    if self.ahb.readBlock(NUC1XX.REGRWPROT_ADDR, 0x01) != [0x00]:
      print 'flashUnlock: Already unlocked'
    else:
      # disable write protection
      self.ahb.writeWord(NUC1XX.REGRWPROT_ADDR, 0x59)
      self.ahb.writeWord(NUC1XX.REGRWPROT_ADDR, 0x16)
      self.ahb.writeWord(NUC1XX.REGRWPROT_ADDR, 0x88)
    
    if self.ahb.readBlock(NUC1XX.REGRWPROT_ADDR, 0x01) != [0x01]:
      raise UnlockFailedException('flachUnlock: Unlock didn\'t work')

    # enable ISP
    self.ahb.writeWord(NUC1XX.ISPCON_ADDR, 0x00000031)

  def changeBS(self):
    val = self.ahb.readWord(NUC1XX.ISPCON_ADDR)
    self.ahb.writeWord(NUC1XX.ISPCON_ADDR, val | 2)

  def issueISPCommand(self, adr, cmd, data):
    if self.ahb.readBlock(NUC1XX.ISPTRG_ADDR, 0x01) != [0x00]:
      raise NotReadyForCommandException('not yet ready for command')
    self.ahb.writeWord(NUC1XX.ISPADR_ADDR, adr)
    self.ahb.writeWord(NUC1XX.ISPCMD_ADDR, cmd)
    self.ahb.writeWord(NUC1XX.ISPDAT_ADDR, data)

    # trigger command execution
    self.ahb.writeWord(NUC1XX.ISPTRG_ADDR, 0x00000001)

    while True:
      # successful execution
      if self.ahb.readBlock(NUC1XX.ISPTRG_ADDR, 0x01) == [0x00]:
        break
      # TODO: for now we assume success, actually verify it
    ispcon = self.ahb.readWord(NUC1XX.ISPCON_ADDR)
    self.ahb.writeWord(NUC1XX.ISPCON_ADDR, ispcon)
    if ispcon & 0x40:
      print 'issueISPCOMMAND: ISP command failed: %08X' % ispcon

  def writeFlash(self, addr, data):
    print 'writing 0x%x to 0x%x' % (data, addr)
    self.issueISPCommand(addr, 0x21, data)

  def readFlash(self, start_addr, length):
    # TODO: maybe implement more efficient reading with only 1 dummy cmd
    for counter in range(0, length, 4):
      addr = start_addr + counter
      self.issueISPCommand(addr, 0x00, 0x00)
      data = self.ahb.readWord(NUC1XX.ISPDAT_ADDR)
      print 'reading 0x%x: 0x%x' % (addr, data)

  def eraseFlash(self, addr):
    self.issueISPCommand(addr, 0x22, 0x00)

  def readRegister(self, register):
    self.ahb.writeWord(NUC1XX.DCRSR_ADDR, register)
    return self.ahb.readWord(NUC1XX.DCRDR_ADDR)

  def writeRegister(self, register, data):
    self.ahb.writeWord(NUC1XX.DCRDR_ADDR, data)
    self.ahb.writeWord(NUC1XX.DCRSR_ADDR, register)

  def readAllRom(self):
    for addr in range(0xfffffffC, 0xffffffff, 0x04):
      print hex(self.ahb.readWord(addr))

  def writeToRam(self):
    for addr in range(0x20000000, 0x200000d0, 0x04):
      print 'writing %s' % hex(addr)
      self.ahb.writeWord(addr, 0xDEADBEEF)

  def readFromRam(self):
    for addr in range(0x20000000, 0x200000d0, 0x04):
      print hex(self.ahb.readWord(addr))

  def readConfig(self):
    self.issueISPCommand(NUC1XX.CONFIG0_ADDR, 0x00, 0x00)
    print 'readConfig: %s' % hex(
        self.ahb.readWord(NUC1XX.CONFIG0_ADDR))

  def writeBinToFlash(self, binstr):
    start_addr = 0x00100000
    assert len(binstr) % 4 == 0
    print 'length: %i' % len(binstr)
    for counter in range(0, len(binstr), 4):
      addr = start_addr + counter
      packed_data = binstr[counter:counter+4]
      data = struct.unpack(">I", packed_data)[0] # TODO: maybe <I
      self.eraseFlash(addr)
      self.writeFlash(addr, data)

def readFlashFile(filename):
  flashfile = open(filename, 'rb')
  return flashfile.read()

