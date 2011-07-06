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
        # unlock main flash
        self.ahb.writeWord(0x400C0000 + 0x008, 0x00000001) # MSC_WRITECTL.WREN <- 1

    def flashErase (self, flash_size):
        # erase page by page
        for i in range(flash_size * 2):
            self.ahb.writeWord(0x400C0000 + 0x010, 0x200 * i)  # MSC_ADDRB <- page address
            self.ahb.writeWord(0x400C0000 + 0x00C, 0x00000001) # MSC_WRITECMD <- LADDRIM -- load address
            self.ahb.writeWord(0x400C0000 + 0x00C, 0x00000002) # MSC_WRITECMD <- ERASEPAGE
            time.sleep(0.03)
            # poll the busy bit until it clears
            while (self.ahb.readWord(0x400C0000 + 0x01C) & 0x1) == 1:
                print "waiting for erase completion..."
                time.sleep(0.01)
            #print "Erased page %d" % i

        # FIXME page-by-page erase is slooooow... implement whole-device erase instead
        # This is done through the AAP (see ref. manual section 6.4)

    def flashProgram (self, vals):
        #self.ahb.writeWord(0x40022010, 0x00000201)
        #efm32.ahb.writeHalfs(0x08000000, vals)
        #self.ahb.writeWord(0x40022010, 0x00000200)
        pass

