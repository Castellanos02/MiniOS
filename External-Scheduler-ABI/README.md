# MiniOS FPPS Scheduler — Standalone Distribution

A drop-in **Fixed-Priority Preemptive Scheduler** (FPPS) for i386
freestanding kernels. Originally written for MiniOS; this directory
re-packages it as a self-contained library you can paste into your own
kernel project.

* 4 priority slots, lowest-numbered READY task wins
* 1 ms quantum driven by the 8253/4 PIT at 1000 Hz
* `task_sleep(ticks)`, `yield()`, full preemption
* Three files: header + C runtime + ASM core
* Public API versioned `1.0.0` (see `MINIOS_SCHEDULER_API_VERSION_*`)

---

## 1. What's in this package

```
Enternally Callable ABI/
├── README.md             ← you are here
├── INTEGRATION.md        ← step-by-step integration guide
├── API_REFERENCE.md      ← full per-function reference (~880 lines)
├── scheduler.h           ← public header — the contract
├── scheduler.c           ← C runtime (task_init, tick, yield, sleep, hw init)
├── scheduler.asm         ← ASM entry points (switch_context, isr_pit)
└── example/
    ├── multiboot_header.asm   ← example boot entry
    ├── linker.ld              ← example linker script
    ├── minimal_kernel.c       ← 80-line example kernel using the scheduler
    └── Makefile               ← example build script
```

The library is the three `scheduler.{h,c,asm}` files. The `example/`
folder shows what a *consumer* project looks like.

---

## 2. Hardware & build requirements

This scheduler is hard-bound to **x86 i386 protected mode**. You cannot
use it on:

| Target          | Supported? |
|-----------------|:----------:|
| i386 (32-bit)   | ✅ |
| x86_64 long mode| ❌ — would need a rewrite of `switch_context` |
| ARM / RISC-V    | ❌ |
| Userland Linux  | ❌ — talks directly to PIC + PIT ports |

You also need:
* `gcc -m32` (or an i386 cross-compiler)
* `nasm` to assemble `scheduler.asm`
* A multiboot 1 loader (GRUB is standard)
* Freestanding compile flags: `-ffreestanding -fno-stack-protector -nostdlib`

The compiler must support C11 (`_Static_assert`). Modern GCC and Clang do.

---

## 3. Quickstart

```bash
# 1. Copy scheduler.{h,c,asm} into your project's source tree.

# 2. Add to your build:
gcc -m32 -ffreestanding -fno-stack-protector -nostdlib -I. \
    -c scheduler.c -o scheduler.o
nasm -f elf32 scheduler.asm -o scheduler_asm.o

# 3. In your kernel_main, bootstrap the scheduler:
```

```c
#include "scheduler.h"

void my_task(void)   { while (1) { /* ... */ task_sleep(100); } }

void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr; if (magic != 0x2BADB002) return;

    idt_install();                 /* set up IDT, wire IRQ0 → isr_pit */
    pic_remap();                   /* PIC: IRQ0 → vector 0x20         */
    pit_init();                    /* PIT: 1000 Hz                    */

    task_init(&g_tasks[0], 0, my_task,   g_task_stacks[0], TASK_STACK_SZ);
    task_init(&g_tasks[1], 1, task_idle, g_task_stacks[1], TASK_STACK_SZ);
    g_ready_mask = 0x03;

    g_tasks[0].state = TASK_RUNNING;
    g_ready_mask    &= ~(uint8_t)0x01;
    g_current_task   = 0;

    static Task dummy;
    switch_context(&dummy, &g_tasks[0]);  /* never returns */
}
```

That's the minimum viable kernel. The `example/` directory has a
runnable expansion of this.

---

## 4. What you provide vs what the scheduler provides

| You write                              | Scheduler provides                          |
|----------------------------------------|---------------------------------------------|
| `kernel_main` entry point              | Everything called *from* `kernel_main`      |
| Multiboot header / boot entry asm      | `switch_context` and `isr_pit` (asm)        |
| Linker script (ELF32 i386, ≥1 MB load) | IDT/PIC/PIT initialisation                  |
| Task body functions (loops, never return) | Task lifecycle: `task_init`, `task_sleep`, `yield` |
| Storage for `Task` TCBs + stacks (or use the supplied `g_tasks[]` + `g_task_stacks[]`) | Tick counter, ready mask, current-task index |
| The bootstrap call to `switch_context(&dummy, &g_tasks[0])` | Default `task_idle` (overridable) |

See **INTEGRATION.md** for the per-function hook surface.

---

## 5. The public API (one-paragraph tour)

* **`task_init(t, priority, entry, stack, stack_size)`** — build a TCB.
  Returns `sched_status_t`. Validates inputs and refuses bad ones.
* **`scheduler_tick()`** — drive one quantum. Called from the PIT ISR
  every 1 ms; also called internally by `yield` and `task_sleep`.
* **`yield()`** — voluntary preemption. Returns when caller is
  rescheduled.
* **`task_sleep(ticks)`** — block for `ticks` ms.
* **`idt_install` / `pic_remap` / `pit_init`** — one-call hardware
  bring-up.
* **`scheduler_get_tick` / `scheduler_get_current_task` /
  `scheduler_get_ready_mask` / `scheduler_get_task(idx)`** — read-only
  accessors (zero-cost inlines).
* **`switch_context(prev, next)`** — raw context switch. You only call
  this once, during bootstrap. After that, the scheduler calls it for you.
* **`task_idle()`** — default `hlt`-loop body. Pass it to `task_init` for
  your lowest-priority slot, or replace it with your own.

Full per-function spec with parameter tables, return codes, calling
context, and worked examples: **API_REFERENCE.md**.

---

## 6. Tick rate / customisation

The PIT is programmed for 1000 Hz (1 tick = 1 ms) via `PIT_DIVISOR = 1193`
in `scheduler.h`. If you need a different rate, edit `PIT_DIVISOR` before
compiling. The relationship:

```
tick_rate_Hz ≈ 1193182 / PIT_DIVISOR
```

`task_sleep(N)` blocks for `N` ticks regardless of rate, so the
numerical argument's meaning changes when you re-tune the PIT.

---

## 7. Where things can go wrong

| Symptom                              | Likely cause |
|--------------------------------------|--------------|
| Triple fault at first `switch_context` | Stack too small, or `entry` function returns. |
| PIT never fires                      | `pic_remap` skipped, or interrupts left masked. |
| Tasks freeze in busy-loops           | Your task body never calls `yield()` or `task_sleep()` — only PIT preemption rescues it. |
| `task_init` returns `SCHED_ERR_*`    | NULL pointer, priority ≥ `NUM_TASKS`, or stack < `MIN_TASK_STACK`. Check `sched_status_str()`. |
| Linker error: undefined `scheduler_tick` | `scheduler.c` not in your link line. |
| Linker error: undefined `switch_context` / `isr_pit` | `scheduler.asm` not assembled or not linked. |
| Random page-faults under preemption  | Reordered `Task` struct (compile-time asserts in `scheduler.h` should catch this). |

---

## 8. Licence

This package is part of the MiniOS project. Use, modify, and redistribute
freely. No warranty.

---

## 9. Further reading

* **INTEGRATION.md** — every hook you must satisfy, in order
* **API_REFERENCE.md** — per-function reference
* `scheduler.h` — the canonical contract (the header IS the schema)
* `example/` — copy-paste starting point
