/* scheduler.h — Public API for the MiniOS Fixed-Priority Preemptive Scheduler
 *
 * Every type, constant, function, and global declared here is part of the
 * externally-callable scheduler API. See scheduler-API.md for the full
 * reference (parameter semantics, return values, calling-context rules,
 * side effects, and worked examples).
 *
 * Target: x86 (i686 / elf32-i386 / 32-bit protected mode, multiboot)
 * Tick frequency: 1000 Hz (1 ms per tick) via PIT channel 0
 * Task model: 4 tasks, priorities 0 (highest) … 3 (lowest), 8 KB stacks
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
/*                                                                           */
/* Semantic version of the scheduler API contract. Increment MAJOR on        */
/* breaking changes, MINOR on backwards-compatible additions, PATCH on       */
/* internal-only fixes. External code may compile-time gate against these:   */
/*                                                                           */
/*   #if MINIOS_SCHEDULER_API_VERSION_MAJOR != 1                             */
/*   #error "Scheduler API major version mismatch"                           */
/*   #endif                                                                  */
/* ========================================================================= */

#define MINIOS_SCHEDULER_API_VERSION_MAJOR  1
#define MINIOS_SCHEDULER_API_VERSION_MINOR  0
#define MINIOS_SCHEDULER_API_VERSION_PATCH  0
#define MINIOS_SCHEDULER_API_VERSION        "1.0.0"

/* ========================================================================= */
/* COMPILE-TIME CONSTANTS                                                    */
/* ========================================================================= */

#define TASK_READY        0u    /* runnable, waiting for the CPU             */
#define TASK_RUNNING      1u    /* currently executing on the CPU            */
#define TASK_SLEEPING     2u    /* blocked until g_tick >= wake_tick         */

#define NUM_TASKS         4     /* hard-coded number of priority slots       */
#define TASK_STACK_SZ     8192  /* per-task stack size, in bytes             */
#define MIN_TASK_STACK    64    /* minimum bytes required by task_init       */

#define PIT_DIVISOR       1193  /* 1193182 Hz / 1193 ≈ 1000 Hz (1 ms tick)   */
#define SNN_WAKE_INTERVAL 1800000UL  /* 30 min × 60 s × 1000 ticks/s         */

#define SCHED_EFLAGS_INIT 0x00000202u  /* IF=1, reserved bit 1 set           */
#define PIT_VECTOR        0x20u        /* IDT vector for IRQ0 after remap    */

/* ========================================================================= */
/* STATUS / ERROR CODES                                                      */
/*                                                                           */
/* The scheduler reports input-validation failures through a small enum.     */
/* SCHED_OK is guaranteed to be zero so `if (task_init(...))` reads as       */
/* "fail if non-zero". Negative values are reserved for hard errors;         */
/* positive values are reserved for soft / advisory statuses.                */
/* ========================================================================= */

typedef enum sched_status {
    SCHED_OK                  =  0,  /* success                              */
    SCHED_ERR_NULL_PTR        = -1,  /* a required pointer arg was NULL      */
    SCHED_ERR_BAD_PRIORITY    = -2,  /* priority >= NUM_TASKS                */
    SCHED_ERR_STACK_TOO_SMALL = -3,  /* stack_size  < MIN_TASK_STACK         */
    SCHED_ERR_BAD_STATE       = -4   /* operation invalid in current state   */
} sched_status_t;

/* Human-readable string for a status code. Returns a pointer to a static
 * string literal — never NULL, never needs freeing. Unknown codes return
 * "unknown scheduler error". */
const char *sched_status_str(sched_status_t s);

/* ========================================================================= */
/* TYPES                                                                     */
/* ========================================================================= */

/* Task Control Block (TCB).
 *
 * The field order is part of the binary ABI: scheduler.asm dereferences
 * `esp` and `ebp` by hard-coded byte offsets (0 and 4). Do NOT reorder.
 */
typedef struct Task {
    uint32_t esp;        /* offset  0 — saved stack pointer    (MUST be first) */
    uint32_t ebp;        /* offset  4 — saved base pointer                     */
    uint32_t state;      /* offset  8 — TASK_READY / RUNNING / SLEEPING        */
    uint8_t  priority;   /* offset 12 — 0 (highest) … 3 (lowest)               */
    uint32_t stack_top;  /* offset 16 — high address of this task's stack      */
    uint32_t wake_tick;  /* offset 20 — tick at which a sleeping task wakes    */
} Task;

/* ABI lock — scheduler.asm reads `esp` and `ebp` by hard-coded byte
 * offsets (0 and 4). If any future edit shifts those fields, the
 * compile fails here rather than silently triple-faulting at boot. */
_Static_assert(offsetof(Task, esp) == 0,
               "Task.esp must be at offset 0 — scheduler.asm depends on it");
_Static_assert(offsetof(Task, ebp) == 4,
               "Task.ebp must be at offset 4 — scheduler.asm depends on it");
_Static_assert(sizeof(uint32_t) == 4,
               "scheduler.asm assumes 32-bit uint32_t");

/* ========================================================================= */
/* GLOBAL STATE                                                              */
/* ========================================================================= */

/* The four task control blocks. Index == priority. */
extern Task               g_tasks[NUM_TASKS];

/* Bitmask of READY tasks. Bit N set ⇔ g_tasks[N].state == TASK_READY. */
extern uint8_t            g_ready_mask;

/* Index (0..NUM_TASKS-1) of the task currently in TASK_RUNNING state. */
extern uint8_t            g_current_task;

/* Monotonic millisecond counter, incremented by scheduler_tick(). */
extern volatile uint32_t  g_tick;

/* Backing storage for each task's stack — 4 × 8 KB, 16-byte aligned. */
extern uint8_t            g_task_stacks[NUM_TASKS][TASK_STACK_SZ];

/* UI gate: when non-zero, task_ui must not consume keyboard input
 * (task_metrics is mid-notification and owns the keystrokes). */
extern volatile uint8_t   g_notification_active;

/* ========================================================================= */
/* ASSEMBLY ENTRY POINTS  (defined in kernel/scheduler.asm, BITS 32)         */
/* ========================================================================= */

/* Save the full register context of `prev`, restore `next`, and jump into
 * wherever `next` was last executing (or its entry function on first call).
 *
 * cdecl, no return value, returns to the caller's frame on the NEW task's
 * stack — meaning execution after this call resumes only when `prev`
 * itself is rescheduled.
 */
void switch_context(Task *prev, Task *next);

/* PIT IRQ0 ISR. Wired into the IDT at vector PIT_VECTOR (0x20).
 * Not intended to be called from C; exposed so the IDT can take its
 * address. Calls scheduler_tick() internally and sends EOI to the PIC.
 */
void isr_pit(void);

/* ========================================================================= */
/* HARDWARE INITIALISATION                                                   */
/* ========================================================================= */

/* Install a single IDT entry. `vec` = 0..255, `handler` = 32-bit linear
 * address. Sets selector 0x08 (GRUB's flat ring-0 code segment) and
 * type 0x8E (present, ring-0, 32-bit interrupt gate — IF cleared on entry).
 */
void idt_set_gate(uint8_t vec, uint32_t handler);

/* Build the 256-entry IDT, wire vector 0x20 → isr_pit, and LIDT it.
 * All other vectors are written as not-present (type 0x0E). Must be
 * called BEFORE enabling interrupts (sti / first pic_remap output).
 */
void idt_install(void);

/* Reinitialise the 8259A PIC pair:
 *   Master IRQ0-7  → IDT vectors 0x20-0x27
 *   Slave  IRQ8-15 → IDT vectors 0x28-0x2F
 * Unmasks IRQ0 only (PIT); masks every other line.
 */
void pic_remap(void);

/* Program PIT channel 0 for ~1000 Hz square-wave (mode 3) using
 * PIT_DIVISOR. Must be called after pic_remap() and before sti.
 */
void pit_init(void);

/* ========================================================================= */
/* CORE SCHEDULER API                                                        */
/* ========================================================================= */

/* Build a fresh Task. After this returns SCHED_OK, the very first
 * switch_context targeting `t` will jump straight into `entry`.
 *
 *   t          — caller-owned TCB to populate (must be non-NULL)
 *   priority   — 0 (highest) … NUM_TASKS-1 (lowest); must be < NUM_TASKS
 *   entry      — task entry function (must be non-NULL, must never return)
 *   stack_buf  — pointer to a stack region (must be non-NULL)
 *   stack_size — size of stack_buf in bytes; must be >= MIN_TASK_STACK
 *
 * EFLAGS is pre-seeded with IF=1 so the PIT can fire as soon as the
 * task is dispatched.
 *
 * Returns:
 *   SCHED_OK                  — task initialised successfully
 *   SCHED_ERR_NULL_PTR        — t, entry, or stack_buf was NULL
 *   SCHED_ERR_BAD_PRIORITY    — priority >= NUM_TASKS
 *   SCHED_ERR_STACK_TOO_SMALL — stack_size < MIN_TASK_STACK
 *
 * On any error code, *t is left untouched.
 */
sched_status_t task_init(Task *t,
                         uint8_t priority,
                         void (*entry)(void),
                         uint8_t *stack_buf,
                         uint32_t stack_size);

/* Drive one scheduler quantum:
 *   1. Increment g_tick
 *   2. Promote any SLEEPING task whose wake_tick has elapsed → READY
 *   3. Pick the lowest-numbered READY task as the new current task
 *   4. If the choice differs from g_current_task, call switch_context()
 *
 * Called from isr_pit every 1 ms; also called by yield() and task_sleep().
 * Safe to call from interrupt context (interrupts are already disabled by
 * the interrupt gate when invoked from isr_pit).
 */
void scheduler_tick(void);

/* Voluntary preemption point. Marks the calling task READY (does NOT
 * sleep it) and runs the scheduler. If a higher-priority task is READY,
 * this call switches to it and returns later, when the caller is
 * rescheduled. If no higher-priority task is ready, returns immediately.
 */
void yield(void);

/* Block the calling task for `ticks` × 1 ms.
 *
 * Sets state = TASK_SLEEPING and wake_tick = g_tick + ticks, then runs
 * the scheduler. Returns once g_tick reaches wake_tick and the caller
 * is rescheduled.
 *
 * Calls scheduler_tick() directly rather than yield() so that the
 * SLEEPING state isn't overwritten with READY before the scheduler sees it.
 */
void task_sleep(uint32_t ticks);

/* ========================================================================= */
/* TASK BODIES  (priority shown in parentheses)                              */
/* ========================================================================= */

/* All four tasks are exposed so they can be invoked, replaced, or wrapped
 * by external code. Each is an infinite loop; none ever returns. */

void task_ui(void);       /* (0) keyboard + screen navigation               */
void task_snn(void);      /* (1) SNN inference, wakes every 30 real minutes */
void task_metrics(void);  /* (2) virtual time + proactive notifications     */
void task_idle(void);     /* (3) hlt loop                                   */

/* ========================================================================= */
/* READ-ONLY ACCESSORS                                                       */
/*                                                                           */
/* Preferred external read path for scheduler state. Direct reads of the     */
/* globals above are also legal but couple callers to the field layout.      */
/* These are header inlines so they compile to a single load.                */
/* ========================================================================= */

static inline uint32_t scheduler_get_tick(void) {
    return g_tick;
}

static inline uint8_t scheduler_get_current_task(void) {
    return g_current_task;
}

static inline uint8_t scheduler_get_ready_mask(void) {
    return g_ready_mask;
}

static inline const Task *scheduler_get_task(uint8_t idx) {
    if (idx >= NUM_TASKS) return (const Task *)0;
    return &g_tasks[idx];
}

#ifdef __cplusplus
}
#endif

#endif /* MINIOS_SCHEDULER_H */
