/* scheduler.c — Standalone runtime for the MiniOS FPPS scheduler.
 *
 * This file plus scheduler.h plus scheduler.asm form the complete
 * library. No external symbols are referenced beyond <stdint.h>,
 * <stddef.h>, and the two ASM exports (switch_context, isr_pit).
 *
 * Port-I/O helpers are `static inline` so they cannot collide with the
 * host kernel's own inb/outb. The IDT helper types are `sched_`-prefixed
 * for the same reason.
 *
 * Build:
 *     gcc -m32 -ffreestanding -fno-stack-protector -nostdlib \
 *         -c scheduler.c -o scheduler_c.o
 *     nasm -f elf32 scheduler.asm -o scheduler_asm.o
 *     ld -m elf_i386 -T linker.ld ... scheduler_c.o scheduler_asm.o ...
 */

#include "scheduler.h"

/* ========================================================================= */
/* GLOBAL STATE  (externally visible — declared in scheduler.h)              */
/* ========================================================================= */

Task               g_tasks[NUM_TASKS];
uint8_t            g_ready_mask   = 0;
uint8_t            g_current_task = 0;
volatile uint32_t  g_tick         = 0;
uint8_t            g_task_stacks[NUM_TASKS][TASK_STACK_SZ] __attribute__((aligned(16)));

/* ========================================================================= */
/* PORT I/O (private — static inline, no symbols emitted)                    */
/* ========================================================================= */

static inline uint8_t sched_inb(uint16_t port) {
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

static inline void sched_outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" :: "a"(val), "Nd"(port));
}

static inline void sched_io_wait(void) {
    sched_outb(0x80, 0x00);  /* POST port — safe throwaway, adds ~1 µs delay */
}

/* ========================================================================= */
/* IDT / PIC / PIT INITIALISATION                                            */
/*                                                                           */
/* All helper structs/globals are `sched_`-prefixed to avoid clashes with    */
/* the host kernel's own IDT bookkeeping (if any).                           */
/* ========================================================================= */

typedef struct __attribute__((packed)) {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t  zero;
    uint8_t  type_attr;
    uint16_t offset_high;
} sched_idt_entry_t;

typedef struct __attribute__((packed)) {
    uint16_t limit;
    uint32_t base;
} sched_idt_pointer_t;

static sched_idt_entry_t   sched_idt_table[256];
static sched_idt_pointer_t sched_idt_ptr;

void idt_set_gate(uint8_t vec, uint32_t handler) {
    sched_idt_table[vec].offset_low  = (uint16_t)(handler & 0xFFFF);
    sched_idt_table[vec].selector    = 0x08;
    sched_idt_table[vec].zero        = 0;
    sched_idt_table[vec].type_attr   = 0x8E;
    sched_idt_table[vec].offset_high = (uint16_t)((handler >> 16) & 0xFFFF);
}

void idt_install(void) {
    for (int i = 0; i < 256; i++) {
        sched_idt_table[i].offset_low  = 0;
        sched_idt_table[i].selector    = 0x08;
        sched_idt_table[i].zero        = 0;
        sched_idt_table[i].type_attr   = 0x0E;
        sched_idt_table[i].offset_high = 0;
    }
    idt_set_gate(PIT_VECTOR, (uint32_t)isr_pit);

    sched_idt_ptr.limit = (uint16_t)(sizeof(sched_idt_table) - 1);
    sched_idt_ptr.base  = (uint32_t)sched_idt_table;
    __asm__ volatile("lidt %0" :: "m"(sched_idt_ptr));
}

void pic_remap(void) {
    sched_outb(0x20, 0x11); sched_io_wait();   /* ICW1: init master           */
    sched_outb(0xA0, 0x11); sched_io_wait();   /* ICW1: init slave            */
    sched_outb(0x21, 0x20); sched_io_wait();   /* ICW2: master base = 0x20    */
    sched_outb(0xA1, 0x28); sched_io_wait();   /* ICW2: slave base  = 0x28    */
    sched_outb(0x21, 0x04); sched_io_wait();   /* ICW3: master slave on IR2   */
    sched_outb(0xA1, 0x02); sched_io_wait();   /* ICW3: slave cascade id = 2  */
    sched_outb(0x21, 0x01); sched_io_wait();   /* ICW4: 8086 mode             */
    sched_outb(0xA1, 0x01); sched_io_wait();
    sched_outb(0x21, 0xFE);                    /* OCW1: unmask IRQ0 only      */
    sched_outb(0xA1, 0xFF);                    /* OCW1: mask all slave IRQs   */
}

void pit_init(void) {
    sched_outb(0x43, 0x36);
    sched_outb(0x40, (uint8_t)(PIT_DIVISOR & 0xFF));
    sched_outb(0x40, (uint8_t)((PIT_DIVISOR >> 8) & 0xFF));
}

/* ========================================================================= */
/* CORE SCHEDULER                                                            */
/* ========================================================================= */

sched_status_t task_init(Task *t, uint8_t priority, void (*entry)(void),
                         uint8_t *stack_buf, uint32_t stack_size) {
    if (!t || !entry || !stack_buf) return SCHED_ERR_NULL_PTR;
    if (priority >= NUM_TASKS)       return SCHED_ERR_BAD_PRIORITY;
    if (stack_size < MIN_TASK_STACK) return SCHED_ERR_STACK_TOO_SMALL;

    uint32_t *sp = (uint32_t *)(stack_buf + stack_size);
    *--sp = (uint32_t)entry;
    uint32_t *ebp_ptr = sp;
    *--sp = 0;
    for (int i = 0; i < 8; i++) *--sp = 0;
    *--sp = SCHED_EFLAGS_INIT;

    t->esp       = (uint32_t)sp;
    t->ebp       = (uint32_t)ebp_ptr;
    t->state     = TASK_READY;
    t->priority  = priority;
    t->stack_top = (uint32_t)(stack_buf + stack_size);
    t->wake_tick = 0;
    return SCHED_OK;
}

const char *sched_status_str(sched_status_t s) {
    switch (s) {
    case SCHED_OK:                  return "ok";
    case SCHED_ERR_NULL_PTR:        return "null pointer argument";
    case SCHED_ERR_BAD_PRIORITY:    return "priority out of range";
    case SCHED_ERR_STACK_TOO_SMALL: return "stack too small";
    case SCHED_ERR_BAD_STATE:       return "invalid scheduler state";
    default:                        return "unknown scheduler error";
    }
}

/* Called from isr_pit (scheduler.asm) every 1 ms, and from yield()/task_sleep().
 * `__attribute__((used))` keeps the linker from GC'ing it under -ffunction-sections. */
void __attribute__((used)) scheduler_tick(void) {
    g_tick++;

    for (int i = 0; i < NUM_TASKS; i++) {
        if (g_tasks[i].state == TASK_SLEEPING && g_tick >= g_tasks[i].wake_tick) {
            g_tasks[i].state = TASK_READY;
            g_ready_mask |= (uint8_t)(1 << i);
        }
    }

    int8_t best = -1;
    for (int i = 0; i < NUM_TASKS; i++) {
        if (g_tasks[i].state == TASK_READY) { best = (int8_t)i; break; }
    }
    if (best < 0) best = NUM_TASKS - 1;

    if ((uint8_t)best == g_current_task) return;

    uint8_t prev = g_current_task;
    if (g_tasks[prev].state == TASK_RUNNING) {
        g_tasks[prev].state  = TASK_READY;
        g_ready_mask |= (uint8_t)(1 << prev);
    }

    g_tasks[best].state  = TASK_RUNNING;
    g_ready_mask &= (uint8_t)~(1 << best);
    g_current_task = (uint8_t)best;

    switch_context(&g_tasks[prev], &g_tasks[best]);
}

void yield(void) {
    g_tasks[g_current_task].state = TASK_READY;
    g_ready_mask |= (uint8_t)(1 << g_current_task);
    scheduler_tick();
}

void task_sleep(uint32_t ticks) {
    uint8_t idx            = g_current_task;
    g_tasks[idx].state     = TASK_SLEEPING;
    g_tasks[idx].wake_tick = g_tick + ticks;
    g_ready_mask &= (uint8_t)~(1 << idx);
    scheduler_tick();
}

/* ========================================================================= */
/* DEFAULT IDLE TASK — overridable by passing your own entry to task_init.   */
/* ========================================================================= */

void task_idle(void) {
    while (1) { __asm__ volatile("hlt"); }
}
