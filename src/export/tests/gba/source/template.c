
#include <gba_console.h>
#include <gba_video.h>
#include <gba_interrupt.h>
#include <gba_systemcalls.h>
#include <gba_input.h>
#include <gba_types.h>
#include "forward.h"
#include <stdio.h>
#include <stdlib.h>

#define IN_EWRAM __attribute__((section(".ewram")))

volatile u16 stopWriteData IN_EWRAM;
volatile u16 stopReadData IN_EWRAM;
volatile int8_t input[10] IN_EWRAM;
volatile int8_t output[10] IN_EWRAM;

int main(void) {

	irqInit();
	irqEnable(IRQ_VBLANK);

	stopWriteData = 1;
	forward(input, output);
	stopReadData = 1;
	consoleDemoInit();

	iprintf("\x1b[10;10HHello World!\n");

	while (1) {
		VBlankIntrWait();
	}
}


