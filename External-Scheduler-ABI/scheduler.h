/* scheduler.h — Public API for the MiniOS Fixed-Priority Preemptive Scheduler
 *
 * Standalone redistribution. Drop these three files into your i386
 * freestanding kernel project:
 *
 *     scheduler.h     this header
 *     scheduler.c     C runtime (task_init, tick, yield, sleep, hw init)
 *     scheduler.asm   ASM entry points (switch_context, isr_pit)
 *
 * See README.md and INTEGRATION.md in the same directory for setup,
 * and API_REFERENCE.md for the full per-function spec.
 *
 * Target: x86 (i686 / elf32-i386 / 32-bit protected mode, multiboot)
 * Tick frequency: 1000 Hz (1 ms per tick) via PIT channel 0
 * Task model: 4 priority slots, lowest-numbered READY task wins
 */

#ifndef MINIOS_SCHEDULER_H
#define MINIOS_SCHEDULER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================= */
/* API VERSION                                                               */
/* ========================================================================= */

#define MINIOS_SCHEDULER_API_VERSION_MAJOR  1
#define MINIOS_SCHEDULER_API_VERSION_MINOR  0
#define MINIOS_SCHEDULER_API_VERSION_PATCH  0
#define MINIOS_SCHEDULER_API_VERSION        "1.0.0"

/* ========================================================================= */
/* COMPILE-TIME CONSTANTS                                                    */
/* ========================================================================= */

#define TASK_READY        0u
#define TASK_RUNNING      1u
#define TASK_SLEEPING     2u

#define NUM_TASKS         4     /* number of priority slots                  */
#define TASK_STACK_SZ     8192  /* recommended per-task stack size, in bytes */
#define MIN_TASK_STACK    64    /* smallest stack accepted by task_init      */

#define PIT_DIVISOR       1193  /* 1193182 Hz / 1193 ≈ 1000 Hz (1 ms tick)   */
#define SCHED_EFLAGS_INIT 0x00000202u  /* IF=1, reserved bit 1 set           */
#define PIT_VECTOR        0x20u        /* IDT vector for IRQ0 after remap    */

/* ========================================================================= */
/* STATUS / ERROR CODES                                                      */
/* ========================================================================= */

typedef enum sched_status {
    SCHED_OK                  =  0,
    SCHED_ERR_NULL_PTR        = -1,
    SCHED_ERR_BAD_PRIORITY    = -2,
    SCHED_ERR_STACK_TOO_SMALL = -3,
    SCHED_ERR_BAD_STATE       = -4
} sched_status_t;

const char *sched_status_str(sched_status_t s);

/* ========================================================================= */
/* TYPES                                                                     */
/* ========================================================================= */

/* Task Control Block (TCB).
 *
 * ABI lock: scheduler.asm reads `esp` and `ebp` by hard-coded byte
 * offsets (0 and 4). Do NOT reorder.
 */
typedef struct Task {
    uint32_t esp;        /* offset  0 — saved stack pointer    (MUST be first) */
    uint32_t ebp;        /* offset  4 — saved base pointer                     */
    uint32_t state;      /* offset  8 — TASK_READY / RUNNING / SLEEPING        */
    uint8_t  priority;   /* offset 12 — 0 (highest) … NUM_TASKS-1 (lowest)     */
    uint32_t stack_top;  /* offset 16 — high address of this task's stack      */
    uint32_t wake_tick;  /* offset 20 — tick at which a sleeping task wakes    */
} Task;

_Static_assert(offsetof(Task, esp) == 0,
               "Task.esp must be at offset 0 — scheduler.asm depends on it");
_Static_assert(offsetof(Task, ebp) == 4,
               "Task.ebp must be at offset 4 — scheduler.asm depends on it");
_Static_assert(sizeof(uint32_t) == 4,
               "scheduler.asm assumes 32-bit uint32_t");

/* ========================================================================= */
/* GLOBAL STATE                                                              */
/* ========================================================================= */

extern Task               g_tasks[NUM_TASKS];
extern uint8_t            g_ready_mask;
extern uint8_t            g_current_task;
extern volatile uint32_t  g_tick;
extern uint8_t            g_task_stacks[NUM_TASKS][TASK_STACK_SZ];

/* ========================================================================= */
/* ASSEMBLY ENTRY POINTS  (defined in scheduler.asm)                         */
/* ========================================================================= */

/* Save `prev`'s CPU context onto its own stack, restore `next`'s, and
 * jump into wherever `next` was last executing. cdecl. */
void switch_context(Task *prev, Task *next);

/* PIT IRQ0 handler. Don't call from C — only take its address for the
 * IDT (idt_set_gate(PIT_VECTOR, (uint32_t)&isr_pit)). */
void isr_pit(void);

/* ========================================================================= */
/* HARDWARE INITIALISATION                                                   */
/* ========================================================================= */

/* Install one IDT gate. vec = 0..255, handler = 32-bit linear address.
 * Selector 0x08, type 0x8E (present, ring-0, 32-bit interrupt gate). */
void idt_set_gate(uint8_t vec, uint32_t handler);

/* Build the 256-entry IDT, wire vector 0x20 → isr_pit, LIDT it. Must
 * be called with interrupts disabled. */
void idt_install(void);

/* Re-init the 8259A PIC pair: master IRQ0–7 → 0x20–0x27, slave 0x28–0x2F.
 * Unmasks IRQ0 only. Call with interrupts disabled. */
void pic_remap(void);

/* Program PIT channel 0 for ~1000 Hz (mode 3). Call after pic_remap. */
void pit_init(void);

/* ========================================================================= */
/* CORE SCHEDULER API                                                        */
/* ========================================================================= */

/* Build a fresh Task. After SCHED_OK, the first switch_context to `t`
 * jumps to `entry`. See API_REFERENCE.md §6 for full semantics. */
sched_status_t task_init(Task    *t,
                         uint8_t  priority,
                         void   (*entry)(void),
                         uint8_t *stack_buf,
                         uint32_t stack_size);

/* One scheduler quantum: tick, wake sleepers, choose successor, maybe
 * switch. Called from isr_pit every 1 ms, and from yield/task_sleep. */
void scheduler_tick(void);

/* Voluntary preemption — marks the current task READY and runs the
 * scheduler. Returns when caller is rescheduled. Task context only. */
void yield(void);

/* Block the current task for `ticks` × 1 ms. Returns when the timer
 * elapses and the caller is rescheduled. Task context only. */
void task_sleep(uint32_t ticks);

/* ========================================================================= */
/* DEFAULT IDLE TASK                                                         */
/*                                                                           */
/* Provided as `hlt`-loop. Use as task body for the lowest priority slot.    */
/* Replace by passing your own function pointer to task_init.                */
/* ========================================================================= */

void task_idle(void);

/* ========================================================================= */
/* READ-ONLY ACCESSORS                                                       */
/* ========================================================================= */

static inline uint32_t scheduler_get_tick(void)         { return g_tick; }
static inline uint8_t  scheduler_get_current_task(void) { return g_current_task; }
static inline uint8_t  scheduler_get_ready_mask(void)   { return g_ready_mask; }
static inline const Task *scheduler_get_task(uint8_t idx) {
    if (idx >= NUM_TASKS) return (const Task *)0;
    return &g_tasks[idx];
}

#ifdef __cplusplus
}
#endif

#endif /* MINIOS_SCHEDULER_H */
