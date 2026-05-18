/* minimal_kernel.c — Smallest useful program demonstrating the scheduler.
 *
 * This is the file YOU write. It supplies:
 *   - kernel_main()              (called by the multiboot header)
 *   - one or more task body functions
 *   - the bootstrap sequence: idt_install / pic_remap / pit_init,
 *     then task_init for each task, then switch_context.
 *
 * The scheduler library provides everything else. See INTEGRATION.md
 * for the full hook surface.
 *
 * What this example does:
 *   - Task A (priority 0, highest) writes 'A' to VGA position (0,0)
 *     every 200 ms.
 *   - Task B (priority 1)           writes 'B' to VGA position (2,0)
 *     every 500 ms.
 *   - Task C (priority 2)           writes 'C' to VGA position (4,0)
 *     every 1 second.
 *   - task_idle (priority 3)        hlt's between interrupts.
 */

#include "scheduler.h"

/* ----- tiny VGA helper (NOT scheduler code — your own) ----- */

static volatile uint16_t * const VGA = (uint16_t *)0xB8000;

static void vga_put(int x, int y, char c, uint8_t color) {
    VGA[y * 80 + x] = ((uint16_t)color << 8) | (uint16_t)c;
}

/* ----- the three task bodies ----- */

static void task_a(void) {
    while (1) {
        static uint8_t flip = 0;
        flip ^= 1;
        vga_put(0, 0, 'A', flip ? 0x0A : 0x02);
        task_sleep(200);
    }
}

static void task_b(void) {
    while (1) {
        static uint8_t flip = 0;
        flip ^= 1;
        vga_put(2, 0, 'B', flip ? 0x0E : 0x06);
        task_sleep(500);
    }
}

static void task_c(void) {
    while (1) {
        static uint8_t flip = 0;
        flip ^= 1;
        vga_put(4, 0, 'C', flip ? 0x0C : 0x04);
        task_sleep(1000);
    }
}

/* ----- bootstrap ----- */

void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr;
    if (magic != 0x2BADB002) return;   /* not a multiboot 1 boot */

    /* 1. Hardware bring-up — order matters. Interrupts are still off. */
    idt_install();
    pic_remap();
    pit_init();

    /* 2. Build each TCB. The scheduler does not run yet. */
    task_init(&g_tasks[0], 0, task_a,    g_task_stacks[0], TASK_STACK_SZ);
    task_init(&g_tasks[1], 1, task_b,    g_task_stacks[1], TASK_STACK_SZ);
    task_init(&g_tasks[2], 2, task_c,    g_task_stacks[2], TASK_STACK_SZ);
    task_init(&g_tasks[3], 3, task_idle, g_task_stacks[3], TASK_STACK_SZ);

    g_ready_mask = 0x0F;   /* mark all four READY */

    /* 3. Promote task 0 to RUNNING and bootstrap into it.
     *    The dummy TCB absorbs the save of this stack frame.
     *    task_init seeded EFLAGS with IF=1, so popf inside
     *    switch_context re-enables interrupts on the way in. */
    g_tasks[0].state = TASK_RUNNING;
    g_ready_mask    &= ~(uint8_t)0x01;
    g_current_task   = 0;

    static Task dummy;
    switch_context(&dummy, &g_tasks[0]);

    /* unreachable */
    __asm__ volatile("cli; hlt");
}
