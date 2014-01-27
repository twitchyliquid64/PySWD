from SWDCommon import *
import sys

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

    def flashErase (self, flash_size, page_size):
        # erase page by page
        sys.stdout.write("   0.0 %") ; sys.stdout.flush()
        for i in range(flash_size * 1024 / page_size): # page size is 512 or 1024
            self.ahb.writeWord(0x400C0000 + 0x010, 0x200 * i)  # MSC_ADDRB <- page address
            self.ahb.writeWord(0x400C0000 + 0x00C, 0x00000001) # MSC_WRITECMD.LADDRIM <- 1
            self.ahb.writeWord(0x400C0000 + 0x00C, 0x00000002) # MSC_WRITECMD.ERASEPAGE <- 1
            while (self.ahb.readWord(0x400C0000 + 0x01C) & 0x1) == 1:
                pass # poll the BUSY bit in MSC_STATUS until it clears
            if i % 8 == 0:
                sys.stdout.write("\b" * 7)
                sys.stdout.write("%5.1f %%" % (100.0 * i / (flash_size * 2)))
                sys.stdout.flush()
        sys.stdout.write("\b" * 7 + "100.0 %\n")

    def flashProgram (self, vals):
        # Write each word one by one .... SLOOOW!
        # (don't bother with checking the busy/status bits as this is so slow it's 
        # always ready before we are anyway)
        sys.stdout.write("   0.0 %") ; sys.stdout.flush()
        addr = 0
        for i in vals:
            self.ahb.writeWord(0x400C0000 + 0x010, addr) # MSC_ADDRB <- starting address
            self.ahb.writeWord(0x400C0000 + 0x00C, 0x1)  # MSC_WRITECMD.LADDRIM <- 1
            self.ahb.writeWord(0x400C0000 + 0x018, i)    # MSC_WDATA <- data
            self.ahb.writeWord(0x400C0000 + 0x00C, 0x8)  # MSC_WRITECMD.WRITETRIG <- 1
            addr += 0x4
            if addr % 0x40 == 0:
                sys.stdout.write("\b" * 7)
                sys.stdout.write("%5.1f %%" % (25.0 * addr / len(vals)))
                sys.stdout.flush()
        sys.stdout.write("\b" * 7 + "100.0 %\n")

