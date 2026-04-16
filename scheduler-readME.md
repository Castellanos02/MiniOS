# MiniOS Fixed-Priority Preemptive Scheduler (FPPS)

## Overview

This document describes the scheduler implementation added to MiniOS. The kernel previously ran in a single-threaded polling loop — no interrupts, no task switching, no real timer. This work replaces that with a real 4-task Fixed-Priority Preemptive Scheduler driven by the x86 Programmable Interval Timer (PIT) at 1000 Hz.

The scheduler allows the SNN (Spiking Neural Network) inference engine to run its 20-timestep spike loop without freezing the UI, keeps the UI responsive at all times, and wires up the neuromorphic hook that wakes the SNN every 30 real minutes.

---

## Files Changed

| File | Type | Description |
|------|------|-------------|
| `kernel/scheduler.asm` | New | 32-bit NASM assembly — `switch_context` and `isr_pit` |
| `kernel/kernel_carplay.c` | Modified | All C scheduler code, task bodies, rewritten `kernel_main` |
| `Makefile` | Modified | `iso-carplay` target now assembles and links `scheduler.asm` |

---

## Architecture

### Priority Hierarchy

| Level | Task | Description |
|-------|------|-------------|
| 0 (highest) | `task_ui` | Handles arrow keys, Enter, screen navigation |
| 1 | `task_snn` | SNN inference engine — neuromorphic hook |
| 2 | `task_metrics` | Virtual time, proactive AI notifications, blink indicator |
| 3 (lowest) | `task_idle` | Executes `hlt` — halts CPU until next interrupt |

The scheduler always runs the lowest-numbered READY task. When the PIT fires (every 1 ms), it checks whether a higher-priority task has become runnable and preempts the current one if so.

### Task Control Block (TCB)

```c
typedef struct {
    uint32_t esp;        // offset  0 — saved stack pointer (MUST be first)
    uint32_t ebp;        // offset  4 — saved base pointer
    uint32_t state;      // offset  8 — TASK_READY / TASK_RUNNING / TASK_SLEEPING
    uint8_t  priority;   // offset 12 — 0 (highest) to 3 (lowest)
    uint32_t stack_top;  // offset 16 — top of task's stack
    uint32_t wake_tick;  // offset 20 — tick at which a sleeping task wakes
} Task;
```

`esp` is at offset 0 because `scheduler.asm` accesses it directly by address with no struct awareness.

Each task gets an 8 KB stack (`g_task_stacks[4][8192]`) allocated in BSS. Total static stack: 32 KB, well within the gap between the kernel at `0x100000` and the VGA buffer at `0xB8000`.

---

## Hardware Initialisation

### IDT (Interrupt Descriptor Table)

`idt_install()` zeroes all 256 32-bit interrupt gate entries and wires IRQ0 (the PIT) to `isr_pit` at vector `0x20`. Gate type `0x8E` (interrupt gate) automatically clears `EFLAGS.IF` on entry, preventing nested PIT interrupts.

```
Vector 0x20 → isr_pit (defined in scheduler.asm)
All other vectors → not-present (type 0x0E)
```

### PIC Remapping

`pic_remap()` reinitialises the 8259A PIC pair to move IRQs away from CPU exception vectors:

```
Master PIC: IRQ0-7  → vectors 0x20-0x27
Slave PIC:  IRQ8-15 → vectors 0x28-0x2F
```

Only IRQ0 (PIT) is unmasked on the master. All other IRQs remain masked.

### PIT Configuration

`pit_init()` configures PIT channel 0 in mode 3 (square wave) with divisor 1193:

```
1193182 Hz / 1193 ≈ 1000 Hz (1 ms per tick)
```

Ports used: `0x43` (command), `0x40` (channel 0 data).

---

## Assembly: `kernel/scheduler.asm`

### `switch_context(Task *prev, Task *next)`

32-bit cdecl calling convention. On entry `prev` is at `[esp+4]`, `next` at `[esp+8]`.

**Save sequence (prev task):**
1. `push ebp; mov ebp, esp` — set up frame so `[ebp+8]`/`[ebp+12]` reach the args
2. `pusha` — pushes all 8 GP registers (32 bytes)
3. `pushf` — pushes EFLAGS (4 bytes)
4. Store current `esp` and `ebp` into `prev->esp` and `prev->ebp`

**Restore sequence (next task):**
1. Load `next->esp` into `esp`, `next->ebp` into `ebp`
2. `popf` — restore EFLAGS (re-enables interrupts via IF=1)
3. `popa` — restore GP registers
4. `pop ebp; ret` — unwind frame, jump to wherever `next` was executing

For a brand-new task, `ret` lands at the task's entry function (set up by `task_init`).

### `isr_pit`

Called by the CPU when IRQ0 fires (vector `0x20`). The CPU has already pushed `EFLAGS`, `CS`, `EIP` onto the interrupted task's stack.

```nasm
isr_pit:
    pusha
    pushf
    call scheduler_tick    ; may call switch_context internally
    mov al, 0x20
    out 0x20, al           ; EOI to master PIC
    popf
    popa
    iret                   ; restores CPU-pushed EIP, CS, EFLAGS
```

If `scheduler_tick` switches tasks, the EOI and `iret` execute on the *new* task's stack — this is intentional and correct, since the PIC just needs EOI before the next interrupt and doesn't care which CPU context sends it.

---

## C Scheduler Functions

### `task_init()`

Builds a fake initial stack frame for each new task so the first context switch into it jumps directly to the task's entry function:

```
[high addr] ← stack_top
[entry_func]        ← ret target
[0]                 ← saved ebp (popped by "pop ebp")
[0 × 8]             ← zero GP registers (popa)
[0x00000202]        ← EFLAGS: IF=1, reserved bit 1 set  ← t->esp
```

`EFLAGS = 0x00000202` is critical — it ensures tasks run with interrupts enabled, which is required for the PIT to fire and for `task_idle`'s `hlt` to wake up.

### `scheduler_tick()`

Called every 1 ms from `isr_pit`, and also directly by `yield()` for cooperative preemption.

1. Increment `g_tick`
2. Wake any task whose `wake_tick <= g_tick` (transition SLEEPING → READY)
3. Scan tasks 0–3 for the first READY one (lowest priority number wins)
4. If the winner differs from `g_current_task`, preempt: mark current READY, mark winner RUNNING, call `switch_context`

### `yield()`

Marks the current task READY and calls `scheduler_tick()`. Used at the end of each task's work unit to give other tasks a chance to run.

### `task_sleep(ticks)`

Marks the current task SLEEPING with `wake_tick = g_tick + ticks`, removes it from the ready mask, and calls `scheduler_tick()` directly. Importantly, it does **not** call `yield()` — doing so would overwrite the SLEEPING state back to READY before the scheduler sees it.

---

## Task Descriptions

### `task_ui` (priority 0)

Extracted from the original `kernel_main` event loop. Handles all keyboard input and screen transitions (`SCREEN_HOME` ↔ `SCREEN_CALENDAR`). Checks `g_notification_active` on each iteration — when a proactive notification is showing, it skips key processing entirely so `task_metrics` can read the response key uncontested.

### `task_snn` (priority 1) — Neuromorphic Hook

Runs the SNN inference (`get_snn_suggestion_wrapper`), adds the result to the calendar, then sleeps for `SNN_WAKE_INTERVAL = 1,800,000` ticks:

```
1,800,000 ticks / 1000 ticks/s = 1800 s = 30 minutes
```

This is the neuromorphic hook: the SNN wakes automatically every 30 real minutes via the PIT, adds a context-aware activity suggestion to the calendar, then goes back to sleep.

### `task_metrics` (priority 2)

Runs every 100 ms (`g_tick` based). Responsibilities:
- Advances virtual ML time via `ml_update_context(100000, ...)` — this drives the simulated clock (hour/minute) displayed in the UI
- Detects calendar events that are 8-10 minutes away and shows a proactive notification overlay
- During a notification: polls for `y`/`n` key with a 300-second tick-based countdown, using `task_sleep(100)` between polls instead of a busy-wait loop
- Drives the blink indicator (`*`) in the bottom-right corner

### `task_idle` (priority 3)

```c
static void task_idle(void) {
    while (1) { __asm__ volatile("hlt"); }
}
```

Halts the CPU until the next interrupt. Since `EFLAGS.IF = 1` at task initialisation, the PIT will always wake it. Without this task the CPU would spin at 100% in a tight loop when no other task is runnable.

---

## Boot Sequence

```
kernel_main()
  │
  ├─ init ML state + calendar
  ├─ idt_install()      — load 256-entry IDT, wire IRQ0 → isr_pit
  ├─ pic_remap()        — move IRQs to 0x20-0x2F, unmask IRQ0
  ├─ pit_init()         — start 1000 Hz timer
  ├─ task_init() × 4   — build stack frames for all tasks
  ├─ draw_home_screen() — initial render before first task runs
  ├─ mark task 0 RUNNING, g_current_task = 0
  ├─ sti                — enable interrupts, PIT starts firing
  └─ switch_context(&dummy, &g_tasks[0])
       └─ jumps into task_ui()  [never returns to kernel_main]
```

The `dummy_task` is a static local TCB used to absorb the save of `kernel_main`'s stack frame. It is never added to `g_ready_mask`, so the scheduler can never schedule it — `kernel_main` effectively terminates at the `switch_context` call.

---

## Build

```bash
# On a Linux machine with nasm, gcc (i686 or cross), and grub-mkrescue:
make iso-carplay      # produces build/minios_carplay.iso
make run-carplay      # boots ISO in QEMU (qemu-system-x86_64)
```

The Makefile `iso-carplay` recipe was updated to add:
```makefile
$(AS) -f elf32 $(KERNEL_DIR)/scheduler.asm -o $(BUILD_DIR)/scheduler.o
```
and include `scheduler.o` in the linker invocation between `multiboot_header.o` and `kernel_carplay.o`.

### Verification

```bash
# Inspect generated code
objdump -d build/minios_carplay.bin | grep -A10 isr_pit
objdump -d build/minios_carplay.bin | grep -A10 switch_context

# Confirm all symbols linked
nm build/minios_carplay.bin | grep ' T ' | grep -E 'isr_pit|switch_context|scheduler_tick|task_'

# Check BSS size (task stacks: 4 × 8 KB = 32 KB)
size build/minios_carplay.bin

# Run with interrupt tracing to confirm 1 ms PIT ticks
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d \
    -d int -no-reboot 2>&1 | head -40
```

Expected: vector `0x20` appears in the trace at ~1 ms intervals with no vector `0x08` (double fault) or `0x0D` (general protection fault).

---

## Design Decisions

**Why 32-bit?** The `iso-carplay` build target compiles with `gcc -m32` and links as `elf32-i386`. The existing `kernel_entry.asm` and `interrupts.asm` are 64-bit but are not linked into this target — only `multiboot_header.asm` (which is already BITS 32) is used. All new assembly is BITS 32 to match.

**Why `task_sleep` calls `scheduler_tick` directly, not `yield`?** `yield()` unconditionally sets the calling task's state to READY before invoking the scheduler. Calling `yield()` from `task_sleep` would overwrite the SLEEPING state that was just set, and the task would immediately be re-scheduled instead of sleeping.

**Why interrupt gates (`0x8E`) instead of trap gates (`0x8F`)?** Interrupt gates clear `EFLAGS.IF` on entry, preventing the PIT from firing a second time while the first ISR is still running. This prevents stack overflow from nested timer interrupts.

**Why is `dummy_task` never in `g_ready_mask`?** `kernel_main`'s stack frame is saved into `dummy_task.esp` by the bootstrap `switch_context` call. Since `dummy_task` is never added to the ready mask, the scheduler cannot pick it, and `kernel_main` never resumes — a clean, intentional one-way handoff to the task system.
