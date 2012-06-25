from SWDCommon import *

flash_base = 0x40023c00

FLASH_PECR = flash_base+0x04
FLASH_PEKEYR = flash_base+0x0C
FLASH_PRGKEYR = flash_base+0x10
FLASH_SR = flash_base+0x18

class STM32:
    def __init__ (self, debugPort):
        self.ahb = MEM_AP(debugPort, 0)

    def halt (self):
        # halt the processor core
        self.ahb.writeWord(0xE000EDF0, 0xA05F0003)

    def unhalt (self):
        # unhalt the processor core
        self.ahb.writeWord(0xE000EDF0, 0xA05F0000)

    def sysReset (self):
        # restart the processor and peripherals
        self.ahb.writeWord(0xE000ED0C, 0x05FA0004)

    def flashUnlock (self):
        """ unlock data EEPROM """
        self.ahb.writeWord(FLASH_PEKEYR, 0x89ABCDEF)
        self.ahb.writeWord(FLASH_PEKEYR, 0x02030405)

    def flashLock(self):
        """ Lock data EEPROM """
        self.ahb.writeWord(FLASH_PECR, 0x1)

    def programUnlock(self):
        """ unlock program memory """
        self.ahb.writeWord(FLASH_PRGKEYR, 0x8C9DAEBF)
        self.ahb.writeWord(FLASH_PRGKEYR, 0x13141516)

    def programLock(self):
        """ lock program memory """
        self.ahb.writeWord(FLASH_PECR, 0x2)

    def flashErase (self, prog, addr):
        """ erase a page of FLASH """
        PROG = 1<<3
        DATA = 1<<4
        ERASE = 1<<9
        # start the mass erase
        v = ERASE | (PROG if prog else 0)
        self.ahb.writeWord(FLASH_PECR, v)
        # check the BSY flag
        while (self.ahb.readWord(FLASH_SR) & 1) == 1:
            print "waiting for erase completion..."
            time.sleep(0.01)
        self.ahb.writeWord(addr, 0x0)
        self.ahb.writeWord(FLASH_PECR, 0x0)

    def flashProgram (self):
        pass

    def flashProgramEnd (self):
        pass
