
#include <gba_console.h>
#include <gba_video.h>
#include <gba_interrupt.h>
#include <gba_systemcalls.h>
#include <gba_input.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {

	irqInit();
	irqEnable(IRQ_VBLANK);

	consoleDemoInit();

	iprintf("\x1b[10;10HHello World!\n");

	while (1) {
		VBlankIntrWait();
	}
}


