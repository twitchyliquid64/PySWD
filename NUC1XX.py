#!/usr/bin/python

# SWD adapter for the Nucon NUC1XX series.

__author__ = 'Pascal Hahn <ph@lxd.bz>'

import struct
import SWDCommon


class Error(Exception):
    pass


class NotReadyForCommandException(Error):
    pass


class UnlockFailedException(Error):
    pass


class FlashDataInvalid(Error):
    pass


class FlashAddressNotAlligned(Error):
    pass


# page numbers refer to: tech. ref. manual NUC100/NUC120, V2.01
class NUC1XX(object):
    CONFIG0_ADDR = 0x00300000

    # pg 483:
    ISPCON_ADDR = 0x5000C000
    ISPADR_ADDR = 0x5000C004
    ISPDAT_ADDR = 0x5000C008
    ISPCMD_ADDR = 0x5000C00C
    ISPTRG_ADDR = 0x5000C010
    DFBADR_ADDR = 0x5000C014  # data flash base address

    # pg 68:
    IPRSTC_ADDR = 0x50000008
    REGWRPROT_ADDR = 0x50000100

    DHCSR_ADDR = 0xE000EDF0

    DCRSR_ADDR = 0xE000EDF4
    DCRDR_ADDR = 0xE000EDF8

    AIRCR_ADDR = 0xE000ED0C

    # pg 472:
    APROM_START = 0
    LDROM_START_ADDR = 0x00100000
    LDROM_SIZE = 0x1000

    USERCONFIG_START = 0x00300000

    # pg 482:
    ISPCMD_PAGE_ERASE = 0x22
    ISPCMD_PROGRAM = 0x21
    ISPCMD_READ = 0x00

    # pg 484f:
    ISPCON_ISPFF = 0x40
    ISPCON_BS = 0x02

    # page 478
    CONFIG0_CBS = 0x01 << 7

    FLASH_PAGESIZE = 0x200

    def __init__(self, debugport):
        self.ahb = SWDCommon.MEM_AP(debugport, 0)

    def halt(self):
        self.ahb.writeWord(NUC1XX.DHCSR_ADDR, 0xA05F0003)

    def unhalt(self):
        self.ahb.writeWord(NUC1XX.DHCSR_ADDR, 0xA05F0001)

    def step(self):
        self.ahb.writeWord(NUC1XX.DHCSR_ADDR, 0xA05F0005)

    def reset(self):
        # pg 72:
        self.ahb.writeWord(NUC1XX.IPRSTC_ADDR, 0x01)

    def registerUnlock(self):
        # pg 101:
        if self.ahb.readBlock(NUC1XX.REGWRPROT_ADDR, 0x01) != [0x00]:
            print 'registerUnlock: Already unlocked'
        else:
            # disable write protection
            self.ahb.writeWord(NUC1XX.REGWRPROT_ADDR, 0x59)
            self.ahb.writeWord(NUC1XX.REGWRPROT_ADDR, 0x16)
            self.ahb.writeWord(NUC1XX.REGWRPROT_ADDR, 0x88)

        if self.ahb.readBlock(NUC1XX.REGWRPROT_ADDR, 0x01) != [0x01]:
            raise UnlockFailedException('flachUnlock: Unlock didn\'t work')

    def enableISP(self):
        # enable ISP
        self.ahb.writeWord(NUC1XX.ISPCON_ADDR, 0x00000031)

    def changeBS(self, bs=True):
        """toggle ISPCON.BS bit:
        True: boot from LDROM
        False: boot from APROM"""
        ispcon = self.ahb.readWord(NUC1XX.ISPCON_ADDR)

        if bs:
            ispcon |= NUC1XX.ISPCON_BS
        else:
            ispcon &= ~NUC1XX.ISPCON_BS

        self.ahb.writeWord(NUC1XX.ISPCON_ADDR, ispcon)

    def changeCBS(self, cbs=False):
        """toggle CONFIG0_CBS:
        True: boot from APROM
        False: boot from LDROM""" 
        config0 = self.readFlashWords(NUC1XX.CONFIG0_ADDR, 1)

        if cbs:
            config0[0] |= NUC1XX.CONFIG0_CBS
        else:
            config0[0] &= ~NUC1XX.CONFIG0_CBS

        self.eraseFlashWords(NUC1XX.CONFIG0_ADDR, 1)
        self.writeFlashWords(NUC1XX.CONFIG0_ADDR, config0)

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
        if self.ahb.readWord(NUC1XX.ISPCON_ADDR) & NUC1XX.ISPCON_ISPFF:
            print 'issueISPCOMMAND: ISP command failed: %08X' % ispcon

    def writeFlashWords(self, start_addr, words):
        cur_addr = start_addr
        for word in words:
            print 'writing 0x%x to 0x%x' % (word, addr)
            self.issueISPCommand(addr, NUC1XX.ISPCMD_PROGRAM, word)
            cur_addr += 4

    def readFlashWords(self, start_addr, word_count):
        # TODO: maybe implement more efficient reading with only 1 dummy cmd
        data = []
        for counter in range(word_count):
            addr = start_addr + (counter * 4)
            self.issueISPCommand(addr, NUC1XX.ISPCMD_READ, 0x00)
            data.append(self.ahb.readWord(NUC1XX.ISPDAT_ADDR))
        return data

    def eraseFlashWords(self, start_addr, word_count):
        for counter in range(word_count):
            addr = start_addr + (counter * 4)
            self.issueISPCommand(addr, NUC1XX.ISPCMD_PAGE_ERASE, 0x00)

    def readRegister(self, register):
        self.ahb.writeWord(NUC1XX.DCRSR_ADDR, register)
        return self.ahb.readWord(NUC1XX.DCRDR_ADDR)

    def writeRegister(self, register, data):
        self.ahb.writeWord(NUC1XX.DCRDR_ADDR, data)
        self.ahb.writeWord(NUC1XX.DCRSR_ADDR, register)

    def writeToRam(self):
        for addr in range(0x20000000, 0x200000d0, 0x04):
            print 'writing %s' % hex(addr)
            self.ahb.writeWord(addr, 0xDEADBEEF)

    def readFromRam(self):
        for addr in range(0x20000000, 0x200000d0, 0x04):
            print hex(self.ahb.readWord(addr))

    def readConfig(self):
        self.issueISPCommand(NUC1XX.CONFIG0_ADDR, 0x00, 0x00)
        return self.ahb.readWord(NUC1XX.ISPDAT_ADDR)

    def writeBinToFlash(self, binstr, start_addr = LDROM_START_ADDR):
        if not start_addr % NUC1XX.FLASH_PAGESIZE == 0:
            raise FlashAddressNotAlligned(
                    'Flash address %x is not aligned with the Pagesize of %i' % (
                        start_addr, NUC1XX.FLASH_PAGESIZE))

        # TODO: maybe we should only allow multiples of FLASH_PAGESIZE,
        # so we won't erase data between the end of the data and
        # the end of the flash page. Could possibly implement partial
        # flash page updates somewhere else.

        if len(binstr) % 4 != 0:
            raise FlashDataInvalid('Flash is not valid / divisible by 4')

        data = []
        for offset in range(0, len(binstr), 4):
            addr = start_addr + offset
            if addr % NUC1XX.FLASH_PAGESIZE == 0:  # reached new page
                self.eraseFlashWords(addr, 1)

            packed_data = binstr[offset:offset + 4]
            data.append(struct.unpack("<I", packed_data)[0])

        self.writeFlashWords(addr, data)

# vim: set tabstop=4 softtabstop=4 shiftwidth=4 textwidth=80 smarttab expandtab:
