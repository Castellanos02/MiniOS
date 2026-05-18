# Integrating the MiniOS FPPS Scheduler

This is the operational guide for wiring the scheduler into your own
kernel. It walks every external symbol, every dependency, and every
call order requirement. Pair it with **API_REFERENCE.md** (per-function
spec) and the runnable **example/** project.

---

## Table of contents

1. [Symbol surface](#1-symbol-surface)
2. [Files you must add to your build](#2-files-you-must-add-to-your-build)
3. [What you must provide](#3-what-you-must-provide)
4. [Required call order](#4-required-call-order)
5. [Per-function hook checklist](#5-per-function-hook-checklist)
6. [Reserved hardware resources](#6-reserved-hardware-resources)
7. [Compile-time options](#7-compile-time-options)
8. [Adapting to non-multiboot environments](#8-adapting-to-non-multiboot-environments)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Symbol surface

After linking `scheduler.c` and `scheduler.asm`, your kernel gains these
symbols:

### Functions you can call

| Symbol             | Source        | Purpose |
|--------------------|---------------|---------|
| `task_init`        | scheduler.c   | Build a TCB |
| `scheduler_tick`   | scheduler.c   | One quantum (also auto-called by PIT) |
| `yield`            | scheduler.c   | Voluntary preemption |
| `task_sleep`       | scheduler.c   | Block N ticks |
| `idt_install`      | scheduler.c   | Build & load IDT (with PIT handler wired) |
| `idt_set_gate`     | scheduler.c   | Write one IDT entry |
| `pic_remap`        | scheduler.c   | Re-init 8259A PIC pair |
| `pit_init`         | scheduler.c   | Program PIT channel 0 for 1000 Hz |
| `switch_context`   | scheduler.asm | Raw context switch (call once at bootstrap) |
| `isr_pit`          | scheduler.asm | PIT IRQ ISR (don't call from C — only its address) |
| `sched_status_str` | scheduler.c   | Status code → static string |
| `task_idle`        | scheduler.c   | Default `hlt`-loop body |

### Inline accessors (zero-cost reads)

| Symbol                          | Returns       |
|---------------------------------|---------------|
| `scheduler_get_tick()`          | `uint32_t`    |
| `scheduler_get_current_task()`  | `uint8_t`     |
| `scheduler_get_ready_mask()`    | `uint8_t`     |
| `scheduler_get_task(idx)`       | `const Task *` (or NULL on bad idx) |

### Globals you can read/write

| Symbol                  | Type                       | Notes |
|-------------------------|----------------------------|-------|
| `g_tasks[NUM_TASKS]`    | `Task[]`                   | TCB array, indexed by priority |
| `g_ready_mask`          | `uint8_t`                  | Bitmask of READY tasks |
| `g_current_task`        | `uint8_t`                  | Index of currently RUNNING task |
| `g_tick`                | `volatile uint32_t`        | Monotonic ms counter |
| `g_task_stacks[][8192]` | `uint8_t[NUM_TASKS][]`     | Backing stacks, 16-byte aligned |

You may write to `g_tasks` and `g_ready_mask` *only* during bootstrap or
inside a function the scheduler is calling for you (an ISR, `yield`,
`task_sleep`). Don't poke them from a busy task running in parallel
with the scheduler.

---

## 2. Files you must add to your build

Three source files come with this package. Add them to your build like
any other source file:

```make
SCHED_DIR := path/to/this/package

$(BUILD)/scheduler.o : $(SCHED_DIR)/scheduler.c $(SCHED_DIR)/scheduler.h
	$(CC) -m32 -ffreestanding -fno-stack-protector -nostdlib \
	      -I$(SCHED_DIR) -c $< -o $@

$(BUILD)/scheduler_asm.o : $(SCHED_DIR)/scheduler.asm
	nasm -f elf32 $< -o $@
```

Link both `.o` files into the kernel binary. The link order doesn't
matter for correctness (no static initialisers), but `scheduler_asm.o`
must come before whichever object holds your `kernel_main` if you
prefer multiboot conventions.

---

## 3. What you must provide

The scheduler library does **not** include any of these — you supply them.

### 3.1 A multiboot entry point

A bit of asm that GRUB jumps to, sets up an initial stack, and calls
into your C code. Canonical form lives in
[`example/multiboot_header.asm`](example/multiboot_header.asm).
The C function it calls (`kernel_main` by convention, but the name is
yours to choose) is where you bootstrap the scheduler.

### 3.2 A linker script

Standard multiboot layout: ELF32 i386, kernel loaded at 1 MB,
multiboot header in its own section first. See
[`example/linker.ld`](example/linker.ld).

### 3.3 Task body functions

Each task is a plain C function with signature `void task(void)` that
**never returns**. The scheduler will never call this function except
via `switch_context`; once it returns, the CPU executes whatever
happens to be on top of the stack — typically garbage → triple fault.

A correct task body always loops:

```c
void my_task(void) {
    while (1) {
        do_one_unit_of_work();
        task_sleep(50);   /* or yield() if you have no time budget */
    }
}
```

### 3.4 The bootstrap call sequence

Inside your `kernel_main`, exactly this order:

```c
idt_install();
pic_remap();
pit_init();

task_init(&g_tasks[0], 0, task_a,    g_task_stacks[0], TASK_STACK_SZ);
task_init(&g_tasks[1], 1, task_b,    g_task_stacks[1], TASK_STACK_SZ);
task_init(&g_tasks[2], 2, task_c,    g_task_stacks[2], TASK_STACK_SZ);
task_init(&g_tasks[3], 3, task_idle, g_task_stacks[3], TASK_STACK_SZ);

g_ready_mask     = 0x0F;
g_tasks[0].state = TASK_RUNNING;
g_ready_mask    &= ~(uint8_t)0x01;
g_current_task   = 0;

static Task dummy;
switch_context(&dummy, &g_tasks[0]);  /* never returns */
```

You can have fewer than four tasks — set the corresponding bits in
`g_ready_mask` and leave the rest at their default `0` state. The idle
slot is the only required one; without it, the CPU will spin at 100 %
whenever every other task is sleeping.

---

## 4. Required call order

```
                 ┌─── your code ───┐
                 │  kernel_main()  │
                 └────────┬────────┘
                          │
                          ▼
           idt_install()  → builds IDT, wires PIT vector
                          │
                          ▼
           pic_remap()    → moves IRQs to 0x20-0x2F, unmasks IRQ0
                          │
                          ▼   ↑ interrupts still off here
           pit_init()     → 1000 Hz square wave on channel 0
                          │
                          ▼
           task_init() × N  → build TCBs
                          │
                          ▼
           promote g_tasks[0] to RUNNING manually
                          │
                          ▼
           switch_context(&dummy, &g_tasks[0])
                          │
                          ▼   ↓ popf inside switch_context turns on IF=1
                  ┌────── task_a() begins ───────┐
                  │   (PIT now firing at 1 kHz)  │
                  └──────────────────────────────┘
```

Skipping any of the first three steps → no PIT, no preemption, system
locks on the first `task_sleep`. Skipping the manual promote → scheduler
sees task 0 as `READY`, demotes from `READY` to `READY`, and the bootstrap
`switch_context` lands on a stack frame the scheduler never recorded.

---

## 5. Per-function hook checklist

This is the integration-relevant subset of the full API reference.
For full parameter/return semantics see API_REFERENCE.md §§4–6.

### 5.1 `task_init(t, priority, entry, stack, stack_size)`

**What you hook up**:
* `t` — pointer to a `Task` you own (typically `&g_tasks[priority]`).
* `entry` — your task body. Must never return.
* `stack` — `uint8_t` buffer ≥ `MIN_TASK_STACK` bytes; recommended
  `g_task_stacks[priority]` (8 KB, 16-byte aligned).
* `stack_size` — must match the buffer's true size in bytes.

**Returns** `SCHED_OK` or one of the `SCHED_ERR_*` codes. On error,
`*t` is left untouched.

### 5.2 `idt_install()`

**Hardware it touches**: writes 256 IDT entries in BSS, then `lidt`.
**Prereqs**: interrupts must be off (CPU starts with IF=0 in protected
mode, so this is automatic at boot). After this call the IDT has
vector 0x20 wired to `isr_pit`; all other vectors are not-present.

**If you need other IDT vectors** (keyboard IRQ1, page-fault handler,
etc.), call `idt_set_gate(vec, handler_addr)` *after* `idt_install`.

### 5.3 `pic_remap()`

**Hardware it touches**: ports 0x20/0x21 (master PIC), 0xA0/0xA1 (slave).
Master IRQ0–7 → vectors 0x20–0x27, slave 0x28–0x2F. **Unmasks IRQ0 only**.

**If you need other IRQs**, write your own mask bytes to ports 0x21 and
0xA1 after `pic_remap`. Don't change the base vectors.

### 5.4 `pit_init()`

**Hardware it touches**: ports 0x43 (command), 0x40 (channel 0 data).
Configures square-wave mode 3 with divisor 1193 → ~1000 Hz.

**To change the tick rate**: edit `PIT_DIVISOR` in `scheduler.h` and
recompile. `task_sleep` arguments are in ticks, not milliseconds, so
recalibrate your call sites when you change this.

### 5.5 `switch_context(prev, next)`

You only call this **once**, during bootstrap, with a throwaway `prev`
TCB. Every other context switch is initiated by `scheduler_tick`. Don't
call it from inside a task body.

### 5.6 `yield()` and `task_sleep(ticks)`

Task-context only. **Never** call from inside an ISR — they manipulate
the ready mask of "the current task," which is meaningless when running
on the ISR stack.

### 5.7 `isr_pit`

You don't call it — the CPU does, on every IRQ0. You only take its
address inside `idt_install`. If you skip `idt_install`, the PIT will
fire but the CPU won't know where to jump → triple fault.

---

## 6. Reserved hardware resources

Don't reuse these from elsewhere in your kernel:

| Resource              | Usage                            |
|-----------------------|----------------------------------|
| IDT vector `0x20`     | PIT ISR                          |
| IDT vectors `0x21–0x2F` | Allocated for other PIC IRQs (free for you to use) |
| Ports `0x20`, `0x21`  | Master PIC                       |
| Ports `0xA0`, `0xA1`  | Slave PIC                        |
| Ports `0x40`, `0x43`  | PIT channels 0 and command       |
| Port `0x80`           | POST port — used by `sched_io_wait` as a throwaway sink |
| IRQ 0                 | PIT timer (unmasked by `pic_remap`) |

All other IRQs are masked after `pic_remap`. Re-enable any you need by
clearing the matching mask bit on port 0x21 (master) or 0xA1 (slave).

---

## 7. Compile-time options

Everything is in `scheduler.h`. To customise:

| Macro              | Default | What it controls |
|--------------------|---------|------------------|
| `NUM_TASKS`        | 4       | Max priority slots. Must fit in `g_ready_mask` (uint8_t, so ≤ 8). |
| `TASK_STACK_SZ`    | 8192    | Default per-task stack size. |
| `MIN_TASK_STACK`   | 64      | Smallest accepted by `task_init`. |
| `PIT_DIVISOR`      | 1193    | PIT divisor → ~1000 Hz tick rate. |
| `SCHED_EFLAGS_INIT`| 0x202   | Initial EFLAGS for new tasks. Bit 9 (IF) must be set. |
| `PIT_VECTOR`       | 0x20    | IDT vector for the PIT ISR. |

Increasing `NUM_TASKS` past 8 requires widening `g_ready_mask` to
`uint16_t` and updating every `(1 << i)` cast.

---

## 8. Adapting to non-multiboot environments

The library does **not** assume multiboot — only:

1. **You enter C code with the CPU in 32-bit protected mode**, with a
   flat ring-0 code segment at selector `0x08` and interrupts disabled.
2. **You have a working stack** when you call `kernel_main`.
3. **GRUB-style multiboot magic check is optional** — `kernel_main` is
   your function, you can call `idt_install` without checking magic.

If your boot path is *not* multiboot (e.g. you wrote your own bootloader,
or you're chainloading from BIOS), you only need to satisfy (1) and (2),
then the bootstrap sequence in §3.4 works identically.

If your code-segment selector is **not** `0x08`, edit `scheduler.c`:
in `idt_set_gate` change `g_idt[vec].selector = 0x08` to your value.

---

## 9. Troubleshooting

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Triple fault at first `switch_context` | Stack alignment, or first task body returns | Use `TASK_STACK_SZ`; ensure task body never returns |
| Triple fault on first PIT tick | `idt_install` not called, or IDT selector wrong | Confirm `idt_install` precedes `switch_context`; check your code segment is at selector 0x08 |
| Interrupts work but no preemption | `pic_remap` skipped → CPU vectors collide with exceptions, or IRQ0 masked | Always call `pic_remap` before `sti` |
| `task_init` returns `SCHED_ERR_*` | Self-explanatory — `printf("%s", sched_status_str(r))` | Fix the offending argument |
| Linker: undefined `scheduler_tick` | Forgot to compile `scheduler.c` | Add it to your build |
| Linker: undefined `switch_context` / `isr_pit` | Forgot to assemble `scheduler.asm` | Add `nasm -f elf32` step |
| Compile: `_Static_assert undefined` | Pre-C11 compiler | Add `-std=c11` (or `-std=gnu11`) |
| Random faults under load | Reordered `Task` struct in scheduler.h | Compile-time asserts should catch this; if you bypassed them, restore the original order |
| `clock_settime`-style time drift | Long sleeps wrap `g_tick` past 2³² | Don't sleep more than ~25 days; if you need longer, split into a loop |

If the static asserts in `scheduler.h` fail, **don't disable them** —
they're catching a real ABI break.
