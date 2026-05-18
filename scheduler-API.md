# MiniOS Scheduler — Public API Reference

**API version**: `1.0.0` (see `MINIOS_SCHEDULER_API_VERSION_*` in
[`kernel/scheduler.h`](kernel/scheduler.h)). The version follows
semver: bump MAJOR on breaking changes, MINOR on additive changes,
PATCH on internal fixes.

This document is the authoritative reference for every externally-callable
component of the MiniOS Fixed-Priority Preemptive Scheduler (FPPS).
For background, architecture notes, and design rationale, see
[`scheduler-readME.md`](scheduler-readME.md). For how this API maps
onto the common "good API" criteria, jump to
[§11 API design conformance](#11-api-design-conformance).

All declarations live in [`kernel/scheduler.h`](kernel/scheduler.h).
Bring them into a translation unit with:

```c
#include "scheduler.h"
```

> **ABI**: 32-bit protected mode, `cdecl`, `elf32-i386`, no SSE alignment
> requirement.
> **Tick rate**: 1000 Hz (1 ms / tick) from PIT channel 0.
> **Task model**: 4 priority slots, lowest-numbered READY task wins.

---

## Table of Contents

1. [Constants](#1-constants)
2. [Types](#2-types)
3. [Global state](#3-global-state)
4. [Assembly entry points](#4-assembly-entry-points)
   * [`switch_context`](#switch_context)
   * [`isr_pit`](#isr_pit)
5. [Hardware initialisation](#5-hardware-initialisation)
   * [`idt_set_gate`](#idt_set_gate)
   * [`idt_install`](#idt_install)
   * [`pic_remap`](#pic_remap)
   * [`pit_init`](#pit_init)
6. [Core scheduler API](#6-core-scheduler-api)
   * [`task_init`](#task_init)
   * [`scheduler_tick`](#scheduler_tick)
   * [`yield`](#yield)
   * [`task_sleep`](#task_sleep)
7. [Task bodies](#7-task-bodies)
   * [`task_ui`](#task_ui)
   * [`task_snn`](#task_snn)
   * [`task_metrics`](#task_metrics)
   * [`task_idle`](#task_idle)
8. [Calling-context matrix](#8-calling-context-matrix)
9. [Worked example — booting the scheduler from external code](#9-worked-example)
10. [Error model](#10-error-model)
11. [API design conformance](#11-api-design-conformance)

---

## 1. Constants

| Name                                | Value         | Type      | Meaning |
|-------------------------------------|---------------|-----------|---------|
| `MINIOS_SCHEDULER_API_VERSION_MAJOR`| `1`           | `int`     | Bumped on breaking changes. |
| `MINIOS_SCHEDULER_API_VERSION_MINOR`| `0`           | `int`     | Bumped on additive changes. |
| `MINIOS_SCHEDULER_API_VERSION_PATCH`| `0`           | `int`     | Bumped on internal fixes. |
| `MINIOS_SCHEDULER_API_VERSION`      | `"1.0.0"`     | `const char *` | String form, useful for logs. |
| `TASK_READY`                        | `0`           | `unsigned`| Task is runnable, waiting for the CPU. |
| `TASK_RUNNING`                      | `1`           | `unsigned`| Task is currently executing. |
| `TASK_SLEEPING`                     | `2`           | `unsigned`| Task is blocked until `g_tick >= wake_tick`. |
| `NUM_TASKS`                         | `4`           | `int`     | Hard-coded number of priority slots. |
| `TASK_STACK_SZ`                     | `8192`        | `int`     | Per-task stack size, in bytes. |
| `MIN_TASK_STACK`                    | `64`          | `int`     | Smallest `stack_size` accepted by `task_init`. |
| `PIT_DIVISOR`                       | `1193`        | `int`     | `1 193 182 Hz / 1193 ≈ 1000 Hz`. |
| `SNN_WAKE_INTERVAL`                 | `1 800 000UL` | `uint32_t`| Ticks in 30 real minutes. |
| `SCHED_EFLAGS_INIT`                 | `0x00000202u` | `uint32_t`| Initial EFLAGS for new tasks (IF=1). |
| `PIT_VECTOR`                        | `0x20u`       | `uint8_t` | IDT vector wired to `isr_pit`. |

All constants are compile-time `#define`s — usable from `#if` directives
and array sizes.

---

## 2. Types

### `Task`

```c
typedef struct Task {
    uint32_t esp;        /* offset  0 — MUST stay first */
    uint32_t ebp;        /* offset  4 */
    uint32_t state;      /* offset  8 — TASK_READY | RUNNING | SLEEPING */
    uint8_t  priority;   /* offset 12 — 0 (highest) .. 3 (lowest)        */
    uint32_t stack_top;  /* offset 16 — high address of the task's stack */
    uint32_t wake_tick;  /* offset 20 — absolute wake-up tick            */
} Task;
```

**ABI lock**: the byte offsets of `esp` and `ebp` are hard-coded inside
`kernel/scheduler.asm`. Re-ordering or inserting fields above `ebp` is a
breaking change.

A `Task` is **caller-owned**. The scheduler stores a pointer to it in
`g_tasks[priority]` and never frees it. Lifetime must outlive the task —
typically `static`/file-scope or a global.

### `sched_status_t`

```c
typedef enum sched_status {
    SCHED_OK                  =  0,
    SCHED_ERR_NULL_PTR        = -1,
    SCHED_ERR_BAD_PRIORITY    = -2,
    SCHED_ERR_STACK_TOO_SMALL = -3,
    SCHED_ERR_BAD_STATE       = -4
} sched_status_t;
```

The unified return type for fallible scheduler entry points. `SCHED_OK`
is guaranteed to be `0`, so the common pattern works:

```c
if (task_init(&t, 0, entry, buf, sizeof buf)) {
    /* failure path */
}
```

`sched_status_str(s)` returns a static string describing `s` (never
NULL, never freed).

---

## 3. Global state

All five globals are declared with C linkage in `scheduler.h` and may be
read from any translation unit. Writes are unsafe except where noted.

| Symbol                  | Type                       | Reads | Writes |
|-------------------------|----------------------------|:-----:|:------:|
| `g_tasks[NUM_TASKS]`    | `Task`                     |  ✅   | scheduler only |
| `g_ready_mask`          | `uint8_t`                  |  ✅   | scheduler only |
| `g_current_task`        | `uint8_t`                  |  ✅   | scheduler only |
| `g_tick`                | `volatile uint32_t`        |  ✅   | `scheduler_tick` only |
| `g_task_stacks[4][8192]`| `uint8_t`                  | rarely | `task_init` writes via pointer |
| `g_notification_active` | `volatile uint8_t`         |  ✅   |  ✅ (cooperative UI flag) |

### Read semantics

* `g_tick` is `volatile` — reads are guaranteed not to be hoisted out of
  spin-wait loops and not to be elided between sequence points.
* `g_ready_mask` and `g_current_task` are updated atomically with respect
  to a running task because preemption only happens at the
  `scheduler_tick → switch_context` boundary, which itself is preceded
  by the relevant mutation.

### `g_notification_active`

Purpose: a single-writer (`task_metrics`), multi-reader cooperative
flag. While `1`, `task_ui` skips its keyboard-handling block so the
keystroke is consumed by `task_metrics` instead. External UI code may
set/clear this flag to take over the keyboard for the duration of a
modal overlay.

---

## 4. Assembly entry points

These two symbols live in [`kernel/scheduler.asm`](kernel/scheduler.asm)
(BITS 32, NASM). They are linked in via the `iso-carplay` Makefile target.

### `switch_context`

```c
void switch_context(Task *prev, Task *next);
```

| Parameter | Type     | Direction | Description |
|-----------|----------|-----------|-------------|
| `prev`    | `Task *` | in/out    | TCB whose CPU state will be saved. Must point to live storage; `prev->esp` and `prev->ebp` are overwritten. |
| `next`    | `Task *` | in        | TCB to dispatch. `next->esp` is loaded into `ESP`, `next->ebp` into `EBP`, and execution unwinds the frame stored there. |

**Returns**: nothing. From the caller's perspective, the call returns
only when `prev` is rescheduled (i.e. when some other task calls
`switch_context(_, prev)`).

**Side effects**:
* Pushes `EBP`, `pusha` (32 B), `pushf` (4 B) onto `prev`'s stack —
  then stores the resulting `ESP`/`EBP` into `prev->esp` / `prev->ebp`.
* Loads `next->esp` / `next->ebp` and pops the saved frame.
* Because `popf` restores EFLAGS from `next`'s stack, the IF flag is
  set/cleared according to whatever was on that stack — typically `1`
  for tasks initialised via `task_init`.

**Calling context**:
* From C: safe.
* From an ISR: safe — `isr_pit` does exactly this.
* Must NOT be called with `prev == next` (no-op but cycles through a
  save/restore round-trip).

**Preconditions**:
* `next` must have a valid frame on its stack, either built by
  `task_init` (first run) or saved by a previous `switch_context`.

---

### `isr_pit`

```c
void isr_pit(void);
```

PIT IRQ0 interrupt service routine. **Do not call this from C** —
it ends with `iret`, which expects a hardware-interrupt stack frame
(EIP/CS/EFLAGS pushed by the CPU). Exposed so the IDT can take its
address:

```c
idt_set_gate(PIT_VECTOR, (uint32_t)&isr_pit);
```

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| (none)    | —    | —         | — |

**Returns**: nothing. Exits via `iret`.

**Side effects**:
* `pusha` + `pushf` on entry, `popf` + `popa` on exit (full GP/EFLAGS save).
* Calls `scheduler_tick()` (C linkage). If `scheduler_tick` switches
  tasks, the EOI + `iret` complete on the new task's stack — this is
  intentional and correct.
* Writes `0x20` to port `0x20` to send End-Of-Interrupt to the master PIC.

---

## 5. Hardware initialisation

These functions program the IDT, PIC, and PIT. They are exposed so that
external boot code can reuse the same initialisation sequence (or
re-program the PIT to a different tick rate by overriding `PIT_DIVISOR`).

### `idt_set_gate`

```c
void idt_set_gate(uint8_t vec, uint32_t handler);
```

| Parameter | Type        | Direction | Description |
|-----------|-------------|-----------|-------------|
| `vec`     | `uint8_t`   | in        | IDT vector (0–255). |
| `handler` | `uint32_t`  | in        | 32-bit linear address of the ISR. |

**Returns**: nothing.

**Side effects**: writes `g_idt[vec]` with:
* `selector  = 0x08` — GRUB's flat ring-0 code segment.
* `type_attr = 0x8E` — present, ring-0, 32-bit interrupt gate (IF is
  cleared on entry, blocking nested PIT interrupts).
* `offset_low/high` derived from `handler`.

**Calling context**: must be called **before** `lidt` (i.e. before
`idt_install` finishes), or with interrupts disabled if patching at runtime.

---

### `idt_install`

```c
void idt_install(void);
```

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| (none)    | —    | —         | — |

**Returns**: nothing.

**Side effects**:
1. Zeroes all 256 IDT entries to "not-present" (type `0x0E`).
2. Calls `idt_set_gate(0x20, (uint32_t)isr_pit)`.
3. Issues `lidt` with the IDT base/limit packed into `g_idtp`.

**Calling context**: kernel boot, with interrupts disabled (`cli`).
Must precede `pic_remap` and `pit_init`. Calling it again at runtime is
safe but will wipe any custom vectors you have installed.

---

### `pic_remap`

```c
void pic_remap(void);
```

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| (none)    | —    | —         | — |

**Returns**: nothing.

**Side effects** (via `outb` to ports `0x20`/`0x21`/`0xA0`/`0xA1`):
* Master PIC: IRQ0–7 → vectors `0x20–0x27`.
* Slave PIC:  IRQ8–15 → vectors `0x28–0x2F`.
* Master mask `0xFE` — IRQ0 (PIT) unmasked, all others masked.
* Slave mask `0xFF`  — all slave IRQs masked.

**Calling context**: kernel boot, after `idt_install`, with interrupts
disabled.

---

### `pit_init`

```c
void pit_init(void);
```

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| (none)    | —    | —         | — |

**Returns**: nothing.

**Side effects** (via `outb` to ports `0x43`/`0x40`):
* Command `0x36` — channel 0, lo/hi access, mode 3 (square wave), binary.
* Divisor low and high bytes of `PIT_DIVISOR` (1193).

**Calling context**: kernel boot, after `pic_remap`. Once `sti` is
executed, IRQ0 will start firing at ~1000 Hz, calling `isr_pit`.

---

## 6. Core scheduler API

### `task_init`

```c
sched_status_t task_init(Task    *t,
                         uint8_t  priority,
                         void   (*entry)(void),
                         uint8_t *stack_buf,
                         uint32_t stack_size);
```

| Parameter    | Type           | Direction | Description |
|--------------|----------------|-----------|-------------|
| `t`          | `Task *`       | out       | Caller-owned TCB to populate. Must be non-NULL. Storage must outlive the task. |
| `priority`   | `uint8_t`      | in        | `0` (highest) .. `NUM_TASKS-1` (lowest). Must be `< NUM_TASKS`. Stored verbatim in `t->priority`. |
| `entry`      | `void(*)(void)`| in        | Task entry function. Must be non-NULL. Must never return; behaviour on return is undefined (the CPU executes whatever is at the top of the stack). |
| `stack_buf`  | `uint8_t *`    | in        | Pointer to a memory region of at least `stack_size` bytes. Must be non-NULL. Typically `g_task_stacks[priority]`. |
| `stack_size` | `uint32_t`     | in        | Size of `stack_buf` in bytes. Must be `>= MIN_TASK_STACK` (64). Recommended `>= TASK_STACK_SZ`. |

**Returns**:

| Code                       | Meaning |
|----------------------------|---------|
| `SCHED_OK` (`0`)           | Task initialised. The next `switch_context` to `t` will jump into `entry`. |
| `SCHED_ERR_NULL_PTR`       | `t`, `entry`, or `stack_buf` was NULL. `*t` untouched. |
| `SCHED_ERR_BAD_PRIORITY`   | `priority >= NUM_TASKS`. `*t` untouched. |
| `SCHED_ERR_STACK_TOO_SMALL`| `stack_size < MIN_TASK_STACK`. `*t` untouched. |

**Side effects**: writes a synthetic initial stack frame to the top of
`stack_buf`:

```
high address ┌──────────────┐ ← stack_buf + stack_size
             │ entry        │ ← ret target (first switch_context jumps here)
             │ 0            │ ← saved EBP
             │ 0 × 8        │ ← popa slots (all GP regs zeroed)
             │ 0x00000202   │ ← popf slot (EFLAGS: IF=1, reserved bit 1)
low address  └──────────────┘ ← t->esp points here
```

Sets `t->state = TASK_READY`, `t->wake_tick = 0`, `t->stack_top =
stack_buf + stack_size`.

**Calling context**: any. Typically called from `kernel_main` (or
equivalent boot path) before the first context switch. Re-initialising
a running task is undefined behaviour — stop it first.

**Errors**: none reported. Out-of-range `priority`, NULL pointers, and
under-sized stacks all silently corrupt scheduler state.

---

### `scheduler_tick`

```c
void scheduler_tick(void);
```

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| (none)    | —    | —         | — |

**Returns**: nothing.

**Semantics** (one pass per call):

1. `g_tick++`.
2. For each task with `state == TASK_SLEEPING` and `g_tick >= wake_tick`:
   set state to `TASK_READY` and set the corresponding bit in
   `g_ready_mask`.
3. Linearly scan `g_tasks[0..NUM_TASKS-1]` for the first `TASK_READY`
   task; that's the "best" choice. If none are READY, fall back to the
   idle task (index `NUM_TASKS - 1`).
4. If "best" equals `g_current_task`, return without switching.
5. Otherwise: demote the previously running task from `RUNNING` →
   `READY` (only if it was actually `RUNNING` — preserves `SLEEPING`),
   promote the chosen task to `RUNNING`, clear it from `g_ready_mask`,
   and call `switch_context(&g_tasks[prev], &g_tasks[best])`.

**Side effects**: mutates `g_tick`, `g_tasks[*].state`, `g_ready_mask`,
`g_current_task`, and may transfer control via `switch_context`.

**Calling context**:
* From `isr_pit` — safe and intended; interrupts are disabled by the
  interrupt gate.
* From `yield()` and `task_sleep()` — safe; the caller has just adjusted
  its own state so the scheduler picks the right successor.
* From arbitrary task code — safe but unusual; equivalent to
  cooperatively yielding while also advancing virtual time by 0.

**Returns to caller**: yes — when the caller's task is rescheduled.

---

### `yield`

```c
void yield(void);
```

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| (none)    | —    | —         | — |

**Returns**: nothing — returns on the same logical thread once the
caller is rescheduled.

**Semantics**:

1. Set `g_tasks[g_current_task].state = TASK_READY`.
2. Set bit `g_current_task` in `g_ready_mask`.
3. Call `scheduler_tick()`.

If no higher-priority task is currently READY, the caller is
immediately picked again and `yield()` returns without doing a context
switch.

**Side effects**: may context-switch; updates `g_ready_mask`.

**Calling context**: only from task code. Calling `yield()` from an ISR
is undefined (it would corrupt the ready mask of whatever task was
interrupted).

**Idiomatic usage**: place at the end of each task's work unit:

```c
void task_my_thing(void) {
    while (1) {
        do_one_unit_of_work();
        yield();
    }
}
```

---

### `task_sleep`

```c
void task_sleep(uint32_t ticks);
```

| Parameter | Type       | Direction | Description |
|-----------|------------|-----------|-------------|
| `ticks`   | `uint32_t` | in        | Number of milliseconds to block (1 tick = 1 ms). `0` is allowed and degenerates to "wake immediately"; ≥ `2^32` ticks ≈ 49.7 days. |

**Returns**: nothing — returns when `g_tick` reaches `wake_tick` *and*
the scheduler reselects the caller.

**Semantics**:

1. `g_tasks[g_current_task].state = TASK_SLEEPING`.
2. `g_tasks[g_current_task].wake_tick = g_tick + ticks`.
3. Clear bit `g_current_task` from `g_ready_mask`.
4. Call `scheduler_tick()` (NOT `yield()` — see design note in
   [`scheduler-readME.md`](scheduler-readME.md)).

**Side effects**: removes the caller from the ready set; the scheduler
will not pick it again until `scheduler_tick` promotes it back to
`READY`.

**Wake-up resolution**: 1 ms (one PIT tick). Actual wake-up may be up to
1 ms late and is also subject to higher-priority preemption.

**Overflow**: `g_tick + ticks` wraps modulo `2^32`. Sleeps that would
straddle the wrap point (currently never reached in normal operation —
~49.7 days uptime) will fire early. Don't sleep that long.

**Calling context**: task code only. Safe to call from within nested
function calls.

---

### Read-only accessors

The header also exposes four `static inline` accessor functions. They
compile to a single load and are the preferred external read path
(direct global reads are still legal but couple the caller to the
field layout).

```c
static inline uint32_t        scheduler_get_tick(void);
static inline uint8_t         scheduler_get_current_task(void);
static inline uint8_t         scheduler_get_ready_mask(void);
static inline const Task     *scheduler_get_task(uint8_t idx);
```

| Function                       | Returns       | Failure mode                  |
|--------------------------------|---------------|-------------------------------|
| `scheduler_get_tick()`         | `g_tick`      | none                          |
| `scheduler_get_current_task()` | `g_current_task` | none                       |
| `scheduler_get_ready_mask()`   | `g_ready_mask`| none                          |
| `scheduler_get_task(idx)`      | `&g_tasks[idx]` (or `NULL` if `idx >= NUM_TASKS`) | NULL on out-of-range index |

All four are safe from any calling context (task / ISR / boot) and from
any IF state — they only read state that the scheduler itself updates.

---

## 7. Task bodies

All four task bodies are infinite loops and never return. They are
exposed for completeness (so external code can wrap them, replace them,
or drive them directly in tests) — typical user code only references
them via `task_init` function pointers.

### `task_ui`

```c
void task_ui(void);   /* priority 0 — highest */
```

**Responsibilities**: read keyboard input via `check_key()`, navigate
between `SCREEN_HOME` and `SCREEN_CALENDAR`, and update the visible
selection. Skips all input handling while `g_notification_active != 0`.

**Yields**: every loop iteration (`yield()`).

**Sleeps**: never.

---

### `task_snn`

```c
void task_snn(void);  /* priority 1 — neuromorphic hook */
```

**Responsibilities**: call `get_snn_suggestion_wrapper()`, push the
resulting suggestion onto `g_events[]`, refresh the calendar display if
it's visible, then sleep.

**Sleeps**: `task_sleep(SNN_WAKE_INTERVAL)` ≈ 30 real minutes per cycle.

**Yields**: never (the long sleep replaces an explicit yield).

---

### `task_metrics`

```c
void task_metrics(void);  /* priority 2 */
```

**Responsibilities**:
* Every 100 ms: advance virtual time via `ml_update_context()` and
  check for upcoming calendar events.
* When an event is 8–10 minutes away, render a proactive notification,
  set `g_notification_active = 1`, and poll for `y`/`n` with a
  300 000-tick (5-minute) timeout, using `task_sleep(100)` between polls.
* Every 500 ms: toggle the bottom-right blink indicator (`*` / blank).

**Sleeps**: `task_sleep(100)` during notification polling, plus brief
visual delays of 300–500 ticks.

**Yields**: end of every loop iteration.

---

### `task_idle`

```c
void task_idle(void);  /* priority 3 — lowest, always READY */
```

**Body**:

```c
void task_idle(void) {
    while (1) { __asm__ volatile("hlt"); }
}
```

`HLT` halts the CPU until the next interrupt. Because `task_init` seeds
EFLAGS with IF=1, the PIT is guaranteed to wake it. Existence of this
task is what prevents 100 % CPU spin when nothing else is runnable.

---

## 8. Calling-context matrix

| Function          | Boot code | Task code | ISR    | With IF = 0 |
|-------------------|:---------:|:---------:|:------:|:-----------:|
| `idt_set_gate`    | ✅        | ⚠ (1)     | ⚠ (1)  | ✅          |
| `idt_install`     | ✅        | ⚠ (1)     | ❌     | ✅          |
| `pic_remap`       | ✅        | ⚠ (1)     | ❌     | ✅          |
| `pit_init`        | ✅        | ✅        | ❌     | ✅          |
| `task_init`       | ✅        | ✅ (2)    | ❌     | ✅          |
| `switch_context`  | ✅ (3)    | ✅        | ✅     | ✅          |
| `scheduler_tick`  | ❌        | ✅        | ✅     | ✅          |
| `yield`           | ❌        | ✅        | ❌     | ❌          |
| `task_sleep`      | ❌        | ✅        | ❌     | ❌          |
| `isr_pit`         | ❌        | ❌        | (CPU)  | (CPU)       |
| `task_*` bodies   | ❌ (4)    | (entry)   | ❌     | ❌          |

Legend:
1. Only with `cli` first — these mutate the IDT/PIC, which races with active interrupts.
2. Only for tasks not currently in `g_tasks[]` or after stopping them.
3. Used once for the bootstrap handoff, with a dummy `prev` TCB.
4. Don't invoke task bodies directly from boot code — install them via `task_init`.

---

## 9. Worked example

Bringing the scheduler up from external code (this is exactly what
`kernel_main` does):

```c
#include "scheduler.h"

void my_kernel_entry(void) {
    /* 1. Interrupt controller + timer */
    idt_install();   /* loads IDT, wires IRQ0 → isr_pit          */
    pic_remap();     /* IRQ0 → vector 0x20, unmask PIT only      */
    pit_init();      /* 1000 Hz square wave on PIT channel 0     */

    /* 2. Tasks */
    task_init(&g_tasks[0], 0, task_ui,      g_task_stacks[0], TASK_STACK_SZ);
    task_init(&g_tasks[1], 1, task_snn,     g_task_stacks[1], TASK_STACK_SZ);
    task_init(&g_tasks[2], 2, task_metrics, g_task_stacks[2], TASK_STACK_SZ);
    task_init(&g_tasks[3], 3, task_idle,    g_task_stacks[3], TASK_STACK_SZ);

    g_ready_mask     = 0x0F;     /* all four tasks READY     */
    g_tasks[0].state = TASK_RUNNING;
    g_ready_mask    &= ~0x01u;
    g_current_task   = 0;

    /* 3. Bootstrap: save kernel_main's frame into a throwaway TCB,
     *    then dispatch task 0. Never returns. */
    static Task dummy_task;
    __asm__ volatile("sti");
    switch_context(&dummy_task, &g_tasks[0]);

    __asm__ volatile("cli; hlt");   /* unreachable */
}
```

Replacing a built-in task with your own:

```c
void my_task(void) {
    while (1) {
        do_thing();
        task_sleep(250);   /* run 4× per second */
    }
}

/* before the bootstrap, after task_init() of the original: */
task_init(&g_tasks[2], 2, my_task, g_task_stacks[2], TASK_STACK_SZ);
```

Polling the global tick from any task:

```c
uint32_t start = g_tick;
while ((g_tick - start) < 500) {     /* wait ~500 ms          */
    yield();                         /* don't busy-wait       */
}
```

(In practice, prefer `task_sleep(500)` over the yield-loop above —
it lets the idle task `hlt` instead of churning the scheduler.)

---

## 10. Error model

The scheduler reports input-validation failures through `sched_status_t`
(see §2). `task_init` is the only entry point that currently returns a
status — every other function either cannot fail given its calling
contract, or is an interrupt/asm entry point where returning a code
would be meaningless.

### Validated paths

| Function    | Possible return codes | Behaviour on error |
|-------------|----------------------|--------------------|
| `task_init` | `SCHED_OK`, `SCHED_ERR_NULL_PTR`, `SCHED_ERR_BAD_PRIORITY`, `SCHED_ERR_STACK_TOO_SMALL` | `*t` left untouched; no global state mutated. |

### Unchecked misuse (caller-enforced contract)

| Misuse                                          | Likely symptom |
|-------------------------------------------------|----------------|
| `task_init` with an entry function that returns | `ret` pops garbage → triple fault. |
| `switch_context(prev, prev)`                    | Wasted cycles, no corruption. |
| `switch_context` with uninitialised `next`      | Triple fault (`popa`/`iret` on garbage). |
| `yield` / `task_sleep` from an ISR              | Wrong task marked READY/SLEEPING. |
| Calling `isr_pit` from C                        | `iret` underflows the stack → triple fault. |
| Re-entering `idt_install` with interrupts on    | Race with in-flight IRQ0. |
| Sleeping > 2³¹ ticks                            | `wake_tick` wraps; task wakes early. |
| Two tasks at the same `priority`                | The later `task_init` overwrites the earlier `g_tasks[]` slot. |

### Idempotency

| Function       | Idempotent? | Notes |
|----------------|-------------|-------|
| `idt_install`  | Yes, with `cli` | Rewrites the same 256-entry table; with interrupts off, this is safe to re-issue. |
| `pic_remap`    | Yes, with `cli` | Re-runs the ICW1–ICW4 sequence; benign duplicate init. |
| `pit_init`     | Yes         | Reprograms channel 0; safe to retune at runtime. |
| `idt_set_gate` | Yes         | Pure write to one IDT slot. |
| `task_init`    | Yes, with care | Safe to re-init a slot *only* if the previous task is not currently `RUNNING` or `SLEEPING`. |

External code that retries hardware bring-up after a fault can safely
re-call `idt_install` → `pic_remap` → `pit_init` in sequence, provided
`cli` is held across the whole sequence.

---

## 11. API design conformance

This API is a **kernel-mode C ABI**, not a web API. Concerns like HTTP
verbs, URL structure, OAuth, HTTPS, JSON payloads, and pagination have
no analog at ring 0 and are not discussed. What follows are the
general-purpose design principles that **do** apply, plus the
ABI-native concerns the web-API world doesn't have to think about.

### 11.1 Predictable structure

Every symbol uses a subsystem prefix so callers can grep by domain:

| Prefix          | Subsystem                                |
|-----------------|------------------------------------------|
| `idt_*`         | Interrupt Descriptor Table               |
| `pic_*`         | 8259A Programmable Interrupt Controller  |
| `pit_*`         | 8253/4 Programmable Interval Timer       |
| `task_*`        | Task lifecycle (init / sleep)            |
| `scheduler_*`   | Scheduler state (accessors)              |
| `sched_*`       | Scheduler types and helpers              |
| `g_*`           | Module globals                           |

Verbs follow create / modify / read shape:
**`task_init`** (create), **`yield` / `task_sleep`** (modify own
state), **`scheduler_get_*`** (read). No verb-shaped symbol pretends to
be a noun and vice-versa.

### 11.2 Standardised response format

All fallible entry points return the same type, `sched_status_t`.
Functions that cannot fail given their contract (`yield`,
`scheduler_tick`, `switch_context`) return `void` honestly — there is
no fake "always-SCHED_OK" return value to mislead readers.

### 11.3 Meaningful status codes

```
SCHED_OK                  =  0   /* success — zero, idiomatic    */
SCHED_ERR_NULL_PTR        = -1   /* hard error                   */
SCHED_ERR_BAD_PRIORITY    = -2
SCHED_ERR_STACK_TOO_SMALL = -3
SCHED_ERR_BAD_STATE       = -4
```

Sign carries semantics: zero = ok, negative = hard error, positive
reserved for soft/advisory codes. `sched_status_str()` produces the
human-readable form.

### 11.4 Preemption & starvation (rate-limiting analog)

FPPS is **intentionally non-aging**. A higher-priority `READY` task
will preempt lower-priority tasks indefinitely. This is a deliberate
real-time guarantee, not a bug — but it means callers wanting
fair-share scheduling must layer a `yield()` budget themselves. The
contract is documented; the behaviour is predictable.

### 11.5 State visibility

The four read-only accessors (`scheduler_get_tick`,
`scheduler_get_current_task`, `scheduler_get_ready_mask`,
`scheduler_get_task`) give consumers enough information to:

* measure their own quantum usage (`tick` delta),
* observe scheduler pressure (`ready_mask`),
* inspect any task's state without coupling to the layout of `g_tasks`.

### 11.6 Idempotency

Every hardware-init function (`idt_install`, `pic_remap`, `pit_init`,
`idt_set_gate`) is safe to re-call under `cli`. `task_init` is safe to
re-call on a slot whose task is not currently `RUNNING` or `SLEEPING`.
See §10 for the full table.

### 11.7 Explicit versioning

`MINIOS_SCHEDULER_API_VERSION_{MAJOR,MINOR,PATCH}` plus a string form
(`MINIOS_SCHEDULER_API_VERSION`) let dependent code compile-time gate:

```c
#if MINIOS_SCHEDULER_API_VERSION_MAJOR != 1
#  error "Scheduler API major version mismatch"
#endif
```

### 11.8 Clear error payloads

Every failing call returns a structured code (`sched_status_t`) and a
matching human-readable string from `sched_status_str()`. Errors leave
caller-owned storage untouched, so retry-after-fix is always safe.

### 11.9 Documentation & examples

* **Reference**: this file (`scheduler-API.md`).
* **Architecture**: [`scheduler-readME.md`](scheduler-readME.md).
* **Header is the schema**: [`kernel/scheduler.h`](kernel/scheduler.h)
  is the single source of truth — every public name in this doc maps
  one-to-one to a declaration there.
* **Runnable example**: `make run-carplay` boots the kernel under QEMU,
  exercising every public entry point on the boot path.
* **Copy-paste snippets**: see §9.

---

### 11.10 ABI-native concerns

These are the binary-contract guarantees the web checklist doesn't
even know to ask about, but which determine whether the assembler,
linker, and CPU all agree at runtime.

| Concern | Guarantee in this header |
|---------|--------------------------|
| **Field layout stability** | `_Static_assert(offsetof(Task, esp) == 0)` and `(Task, ebp) == 4` are checked at compile time. Reordering the struct fails to build instead of silently triple-faulting at boot. |
| **Word-size assumption** | `_Static_assert(sizeof(uint32_t) == 4)` — the asm assumes 32-bit `uint32_t`; mismatch fails the build. |
| **Calling convention** | `cdecl` (i386 System V): args pushed right-to-left on the stack, caller cleans up. `EAX`, `ECX`, `EDX` are caller-saved; `EBX`, `ESI`, `EDI`, `EBP` are callee-saved. `switch_context` saves/restores **all** GP registers + EFLAGS because it crosses task boundaries. |
| **Symbol linkage** | All public symbols are plain C linkage — `extern "C"` guard for C++ inclusion, no name mangling. Symbol names in the header equal symbol names in the linked binary. |
| **Storage ownership** | Zero hidden allocation. Every `Task` and every stack buffer is caller-owned; the scheduler stores pointers, never copies, never frees. |
| **Alignment** | `g_task_stacks` is `__attribute__((aligned(16)))` — satisfies the i386 SysV 16-byte stack alignment expected at function entry. |
| **Const-correctness** | `scheduler_get_task` returns `const Task *` so external code can read TCB state without acquiring write capability to scheduler-internal fields. |
| **Reentrancy & IRQ safety** | Explicit per-function matrix in §8 lists which entry points are safe from task context, ISR context, and with `IF=0`. |
| **Header self-containment** | `scheduler.h` includes only `<stdint.h>` and `<stddef.h>`. Any translation unit can `#include "scheduler.h"` without dragging in other kernel headers, and the include guard (`MINIOS_SCHEDULER_H`) makes multiple inclusion safe. |
| **Volatile correctness** | Globals updated from ISR context (`g_tick`) are declared `volatile` so compiler hoisting can't elide their reads in spin-waits. |
| **Bit-stable enum values** | `sched_status_t` members have explicit, fixed integer values — adding new codes never renumbers old ones, so a `.o` built against an older header still works at link time. |

### 11.11 Out of scope

Three commonly-listed concerns are excluded by design, not oversight:

* **Authentication** — there is no second party at ring 0; everything
  in this process is one privilege domain.
* **Authorisation** — same reason.
* **Transport encryption** — there is no transport. Function calls are
  CPU instructions, not network packets.

These will become live concerns the day MiniOS grows a userland and a
syscall boundary; at that point the syscall layer (not this header) is
where they belong.
