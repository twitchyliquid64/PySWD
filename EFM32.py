from SWDCommon import *

class EFM32:
    def __init__ (self, debugPort):
        self.ahb = MEM_AP(debugPort, 0)

    #--------------------------------------------------------------------------
    # Cortex M3 stuff

    def halt (self):
        # halt the processor core
        self.ahb.writeWord(0xE000EDF0, 0xA05F0003)

    def unhalt (self):
        # unhalt the processor core
        self.ahb.writeWord(0xE000EDF0, 0xA05F0000)

    def sysReset (self):
        # restart the processor and peripherals
        self.ahb.writeWord(0xE000ED0C, 0x05FA0004)

    #--------------------------------------------------------------------------
    # EFM32-specific stuff

    def flashUnlock (self):
        ## unlock main flash
        self.ahb.writeWord(0x400C0000 + 0x008, 0x00000001) # MSC_WRITECTL.WREN <- 1

    def flashErase (self, flash_size):
        ## start the mass erase
        #self.ahb.writeWord(0x40022010, 0x00000204)
        #self.ahb.writeWord(0x40022010, 0x00000244)
        ## check the BSY flag
        #while (self.ahb.readWord(0x4002200C) & 1) == 1:
        #    print "waiting for erase completion..."
        #    time.sleep(0.01)
        #self.ahb.writeWord(0x40022010, 0x00000200)
        pass

    def flashProgram (self):
        #self.ahb.writeWord(0x40022010, 0x00000201)
        pass

    def flashWrite (self, vals):
        #efm32.ahb.writeHalfs(0x08000000, vals)
        pass

    def flashProgramEnd (self):
        #self.ahb.writeWord(0x40022010, 0x00000200)
        pass

