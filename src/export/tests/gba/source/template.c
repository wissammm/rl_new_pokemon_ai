
#include <gba_console.h>
#include <gba_video.h>
#include <gba_interrupt.h>
#include <gba_systemcalls.h>
#include <gba_input.h>
#include <gba_types.h>
#include <gba_timers.h>
#include "tests.h"

#include <gba.h>

#ifndef TIMER_ENABLE
#define TIMER_ENABLE (1 << 7)
#endif

#ifndef TIMER_IRQ
#define TIMER_IRQ (1 << 6)
#endif

#ifndef TIMER_DIV_64
#define TIMER_DIV_64 (2 << 0)
#endif

// #include "forward.h"
#include "input_data.h"
#include "test_array.h"
// #include "_matmul_2_matmuladdfusion_fused_weights.h"

#include <stdio.h>
#include <stdlib.h>

#define IN_EWRAM __attribute__((section(".ewram")))
#define IN_IWRAM __attribute__((section(".iwram")))

volatile u16 stopWriteData IN_EWRAM;
volatile u16 stopReadData IN_EWRAM;
volatile int8_t input[1024] IN_EWRAM;
volatile int8_t output[10] IN_EWRAM;

int main(void)
{

    irqInit();
    irqEnable(IRQ_VBLANK);
    consoleDemoInit();


   

    iprintf("\x1b[10;10HInference begin!\n");
    stopWriteData = 1;
    // forward(input, output);
    stopReadData = 1;

    iprintf("\x1b[10;10HHello World!\n");

    while (1)
    {
        VBlankIntrWait();
    }
}
