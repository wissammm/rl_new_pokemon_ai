#ifndef TESTS_H
#define TESTS_H

#include <gba_console.h>
#include <gba_video.h>
#include <gba_interrupt.h>
#include <gba_systemcalls.h>
#include <gba_input.h>
#include <gba_types.h>
#include <gba_timers.h>

#include <gba_dma.h>
#include <gba.h>

#include <stdio.h>
#include "test_array.h"

#ifndef TIMER_DIV_64
#define TIMER_DIV_64 (2 << 0)
#endif

#ifndef TIMER_ENABLE
#define TIMER_ENABLE (1 << 7)
#endif

#ifndef TIMER_IRQ
#define TIMER_IRQ (1 << 6)
#endif

#ifndef TIMER_DIV_64
#define TIMER_DIV_64 (2 << 0)
#endif

#ifndef CPU_FAST_SET_32BIT
#define CPU_FAST_SET_32BIT (1 << 24)
#endif

#ifndef DMA_32BIT
#define DMA_32BIT (1 << 26)
#endif

#define IN_EWRAM __attribute__((section(".ewram")))
#define IN_IWRAM __attribute__((section(".iwram")))

int8_t buffer_iwram[32] IN_IWRAM;
int8_t buffer_ewram[32] IN_EWRAM;

static inline u32 timer_start(int timer_id)
{
    REG_TM3CNT_L = 0;
    REG_TM3CNT_H = 0;
    REG_TM3CNT_H = TIMER_START | TIMER_DIV_64;
    return 0;
}

static inline u32 timer_stop(int timer_id)
{
    REG_TM3CNT_H = REG_TM3CNT_H & ~TIMER_START;
    return REG_TM3CNT_L;
}

static inline int8_t test_load_from_rom()
{
    volatile int8_t a = 0;
    for (int i = 0; i < 100; ++i)
    {
        for (int j = 0; j < 32768; ++j)
        {
            a = tests_array[j];
            a = a + j * 0;
        }
        a = 0;
    }
    return a;
}

static inline int8_t test_load_from_rom_with_cpuFastSet()
{
    volatile int8_t a = 0;
    for (int i = 0; i < 100; ++i)
    {
        for (int j = 0; j < 32768; j += 32)
        {
            CpuFastSet(
                &tests_array[j],              // Source
                buffer_iwram,                 // Destination
                (32 / 4) | CPU_FAST_SET_32BIT // 8 transferts de 32-bit
            );

            for(int k = 0; k < 32; k ++) {
                a += buffer_iwram[k] * j * 0;
            }
        }
        a = 0;
    }
    return a;
}
static inline int8_t test_load_from_rom_to_iwram_with_dma()
{
    volatile int8_t a = 0;  // Prevent optimization
    for (int i = 0; i < 100; ++i)
    {
        for (int j = 0; j < 32768; j += 32)
        {
            REG_DMA3SAD = (u32)&tests_array[j];
            REG_DMA3DAD = (u32)buffer_iwram;
            REG_DMA3CNT = (32 / 4) | DMA_ENABLE | DMA_32BIT | DMA_SRC_INC | DMA_DST_INC;
            while (REG_DMA3CNT & DMA_ENABLE);

            // ✅ Actually touch the result
            for(int k = 0; k < 32; k ++) {
                a += buffer_iwram[k] * j * 0;
            }
        }
        a = 0;
    }
    return a;
}

static inline int8_t test_load_rom_to_ewram_and_ewram_to_iwram_with_dma()
{
    volatile int8_t a = 0;
    for (int i = 0; i < 100; ++i)
    {
        REG_DMA3SAD = (u32)&tests_array[0];
        REG_DMA3DAD = (u32)buffer_iwram;
        REG_DMA3CNT = (32 / 4) | DMA_ENABLE | DMA_32BIT | DMA_SRC_INC | DMA_DST_INC;
        while (REG_DMA3CNT & DMA_ENABLE);

        for (int j = 32; j < 32768; j += 32)
        {
            // ROM -> EWRAM
            REG_DMA3SAD = (u32)&tests_array[j];
            REG_DMA3DAD = (u32)buffer_ewram;
            REG_DMA3CNT = (32 / 4) | DMA_ENABLE | DMA_32BIT | DMA_SRC_INC | DMA_DST_INC;
            while (REG_DMA3CNT & DMA_ENABLE);

            // EWRAM -> IWRAM
            REG_DMA3SAD = (u32)buffer_ewram;
            REG_DMA3DAD = (u32)buffer_iwram;
            REG_DMA3CNT = (32 / 4) | DMA_ENABLE | DMA_32BIT | DMA_SRC_INC | DMA_DST_INC;
            while (REG_DMA3CNT & DMA_ENABLE);

            for(int k = 0; k < 32; k ++) {
                a += buffer_iwram[0] * j * 0;
            }
        }
        a = 0;
    }
    return a;
}


// All tests
static inline int all_tests()
{
    u32 start_time, end_time;

    iprintf("Running tests...\n");

    // Test 1
    // start_time = timer_start(3);
    // test_load_from_rom();
    // end_time = timer_stop(3);
    // iprintf("ROM -> CPU : %lu cycles\n", end_time);

    // Test 2
    start_time = timer_start(3);
    test_load_from_rom_with_cpuFastSet();
    end_time = timer_stop(3);
    iprintf("ROM -> IWRAM CPS: %lu cycles\n", end_time);

    // Test 3
    start_time = timer_start(3);
    test_load_from_rom_to_iwram_with_dma();
    end_time = timer_stop(3);
    iprintf("ROM -> IW DMA: %lu cycles\n", end_time);

    // Test 4
    start_time = timer_start(3);
    test_load_rom_to_ewram_and_ewram_to_iwram_with_dma();
    end_time = timer_stop(3);
    iprintf("ROM -> EW -> IW 2DMA: %lu cycles\n", end_time);

    return 0;
}


#endif // TESTS_H