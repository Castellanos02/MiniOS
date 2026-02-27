# MiniOS Architecture Diagram

## System Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ VGA Text Mode Display (80x25)                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐     │  │
│  │  │ Header: "MiniOS - Neural Activity Suggester"       │     │  │
│  │  ├─────────────────────────────────────────────────────┤     │  │
│  │  │ Main Panel:                                         │     │  │
│  │  │  • Current Time: Monday, 10:30 AM                  │     │  │
│  │  │  • Suggested Activity: "Take a 15-min walk"       │     │  │
│  │  │  • Inference Latency: 15ms                         │     │  │
│  │  │  • Actions: [A]ccept [R]eject [I]gnore            │     │  │
│  │  ├─────────────────────────────────────────────────────┤     │  │
│  │  │ Status Bar: CPU 12% | Memory 2.5MB | Logs 42/1000 │     │  │
│  │  └─────────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      GUI FRAMEWORK (gui.c)                           │
│  ┌───────────────┬───────────────┬────────────────┬──────────────┐  │
│  │ draw_header() │ draw_panel()  │ draw_status()  │ draw_notif() │  │
│  └───────────────┴───────────────┴────────────────┴──────────────┘  │
│                                   ↓                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Event Loop:                                                   │  │
│  │  • Read keyboard input                                        │  │
│  │  • Update display (10Hz)                                      │  │
│  │  • Call Python runtime for inference                          │  │
│  │  • Log feedback                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│               PYTHON RUNTIME / SNN MODEL (python_runtime.c)          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ SNN Model State:                                              │  │
│  │  • weights[10][10]      - Neural network weights             │  │
│  │  • biases[10]           - Neuron biases                      │  │
│  │  • activity_scores[20]  - Current activity rankings          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                   ↓                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Inference Pipeline:                                           │  │
│  │                                                               │  │
│  │  1. Extract Features from Calendar Context                   │  │
│  │     ┌──────────────────────────────────────┐                │  │
│  │     │ Hash("Monday, 10:30 AM, Feb 2026")  │                │  │
│  │     │         ↓                             │                │  │
│  │     │ [0.2, -0.5, 0.8, ..., 0.1]          │                │  │
│  │     │   (10 features)                      │                │  │
│  │     └──────────────────────────────────────┘                │  │
│  │                    ↓                                          │  │
│  │  2. Forward Pass Through Network                             │  │
│  │     ┌──────────────────────────────────────┐                │  │
│  │     │ Input Layer (10 neurons)             │                │  │
│  │     │         ↓                             │                │  │
│  │     │ Hidden = sigmoid(Weights × Input + Bias)             │  │
│  │     │         ↓                             │                │  │
│  │     │ Hidden Layer (10 neurons)            │                │  │
│  │     └──────────────────────────────────────┘                │  │
│  │                    ↓                                          │  │
│  │  3. Update Activity Scores                                   │  │
│  │     ┌──────────────────────────────────────┐                │  │
│  │     │ For each of 20 activities:           │                │  │
│  │     │   score = avg(hidden_layer)          │                │  │
│  │     │   new_score = 0.7×old + 0.3×score   │                │  │
│  │     └──────────────────────────────────────┘                │  │
│  │                    ↓                                          │  │
│  │  4. Apply Feedback Learning                                  │  │
│  │     ┌──────────────────────────────────────┐                │  │
│  │     │ Review last 100 feedback logs:       │                │  │
│  │     │   if activity was accepted:          │                │  │
│  │     │     score += 0.1                     │                │  │
│  │     │   if activity was rejected:          │                │  │
│  │     │     score -= 0.1                     │                │  │
│  │     └──────────────────────────────────────┘                │  │
│  │                    ↓                                          │  │
│  │  5. Select Best Activity                                     │  │
│  │     ┌──────────────────────────────────────┐                │  │
│  │     │ best = argmax(activity_scores)       │                │  │
│  │     │ if random() < 0.2:                   │                │  │
│  │     │   best = random_activity()           │                │  │
│  │     │ return activities[best]              │                │  │
│  │     └──────────────────────────────────────┘                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                   ↓                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Logging System:                                               │  │
│  │  • Store feedback_logs[1000]                                  │  │
│  │  • Each log: {activity, feedback, timestamp, metrics}         │  │
│  │  • Calculate accuracy = accepts / total                       │  │
│  │  • Export to CSV                                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        KERNEL LAYER (kernel_main.c)                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Interrupt Handling:                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │  │
│  │  │ Timer (IRQ0) │  │ Keyboard     │  │ System Call  │       │  │
│  │  │ 100Hz ticks  │  │ (IRQ1)       │  │ Interface    │       │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Memory Management:                                            │  │
│  │  • Heap: 0x100000 - 0x1100000 (16MB)                        │  │
│  │  • kmalloc() - Simple bump allocator                         │  │
│  │  • Track allocation: heap_ptr                                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ I/O Management:                                               │  │
│  │  • VGA Buffer: 0xB8000                                       │  │
│  │  • Keyboard: Port 0x60                                       │  │
│  │  • Timer: Port 0x40                                          │  │
│  │  • PIC: Ports 0x20, 0xA0                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Performance Monitoring:                                       │  │
│  │  • CPU usage: (busy_ticks / total_ticks) × 100              │  │
│  │  • Memory usage: heap_ptr - HEAP_START                       │  │
│  │  • Timer ticks: Incremented at 100Hz                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      BOOTLOADER (boot.asm)                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Boot Sequence:                                                │  │
│  │                                                               │  │
│  │  1. BIOS loads bootloader at 0x7C00                          │  │
│  │  2. Enable A20 line (access >1MB memory)                     │  │
│  │  3. Load GDT (Global Descriptor Table)                       │  │
│  │  4. Switch to protected mode (32-bit)                        │  │
│  │  5. Setup paging for long mode                               │  │
│  │  6. Switch to long mode (64-bit)                             │  │
│  │  7. Load kernel from disk at 0x1000                          │  │
│  │  8. Jump to kernel_main()                                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          HARDWARE                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ x86_64 CPU:                                                   │  │
│  │  • Long mode (64-bit)                                        │  │
│  │  • Interrupts enabled                                        │  │
│  │  • Timer @ 100Hz                                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Memory Layout:                                                │  │
│  │  0x00000000 - 0x00007BFF : Real mode                        │  │
│  │  0x00007C00 - 0x00007DFF : Bootloader                       │  │
│  │  0x00001000 - 0x00010000 : Kernel code                      │  │
│  │  0x00070000 - 0x00074000 : Page tables                      │  │
│  │  0x000B8000 - 0x000B8FA0 : VGA text buffer                  │  │
│  │  0x00100000 - 0x01100000 : Heap (16MB)                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Devices:                                                      │  │
│  │  • Keyboard (PS/2)                                           │  │
│  │  • Timer (PIT)                                               │  │
│  │  • VGA Text Mode (80x25)                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow for User Interaction

```
User Presses 'A' (Accept)
    ↓
Keyboard Hardware
    ↓
Keyboard Interrupt (IRQ1)
    ↓
ISR Handler (interrupts.asm)
    ↓
keyboard_handler() (kernel_main.c)
    ↓
Keyboard Buffer (FIFO)
    ↓
gui_main_loop() (gui.c)
    ↓
keyboard_getchar()
    ↓
Process 'A' key
    ↓
python_log_feedback(activity, "accept")
    ↓
Update feedback_logs[]
Adjust activity_scores[]
    ↓
python_run_inference()
    ↓
Extract features
Forward pass through SNN
Select new activity
    ↓
Update GUI display
Show notification: "Activity accepted!"
    ↓
Return to event loop
```

## Logging Data Flow

```
User Interaction
    ↓
Feedback Captured
    ↓
┌─────────────────────────────────────┐
│ FeedbackLog Structure:              │
│  • activity: "Take a walk"          │
│  • feedback: "accept"               │
│  • timestamp: 1708088400            │
│  • cpu_usage: 12.3%                 │
│  • memory_used: 2.45 MB             │
│  • latency_ms: 15                   │
└─────────────────────────────────────┘
    ↓
Stored in feedback_logs[] array
    ↓
Used for:
    ├─ Model Learning (last 100 logs)
    ├─ Accuracy Calculation
    ├─ Performance Analysis
    └─ CSV Export
```

## Learning Feedback Loop

```
Initial Suggestion: "Read a book"
    ↓
User: [R] Reject
    ↓
activity_scores["Read a book"] -= 0.1
    ↓
New Suggestion: "Take a walk"
    ↓
User: [A] Accept
    ↓
activity_scores["Take a walk"] += 0.1
    ↓
Similar Context Next Time
    ↓
Higher probability of suggesting:
  • "Take a walk" (recently accepted)
  • Other physical activities (pattern learned)
Lower probability of suggesting:
  • "Read a book" (recently rejected)
  • Other sedentary activities
```

## File Organization

```
minios/
├── boot/
│   └── boot.asm              512 bytes    Bootloader
├── kernel/
│   ├── kernel_main.c         2.5 KB       Main kernel
│   ├── interrupts.asm        1 KB         ISR handlers
│   └── linker.ld             500 bytes    Linker script
├── gui/
│   └── gui.c                 5 KB         GUI framework
├── python/
│   └── python_runtime.c      6 KB         SNN model
├── build/
│   ├── boot.bin             512 bytes    Compiled bootloader
│   ├── kernel.bin           ~50 KB       Compiled kernel
│   └── minios.img           1 MB         Full OS image
├── minios_simulator.c        17 KB        Linux simulator
└── minios_simulator          26 KB        Compiled simulator
```

## Build Process

```
Source Files
    ↓
┌─────────────────────────────────────┐
│ boot.asm                            │
│    ↓ NASM (assembler)               │
│ boot.bin (512 bytes)                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ interrupts.asm                      │
│    ↓ NASM (assembler)               │
│ interrupts.o                        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ kernel_main.c, gui.c,               │
│ python_runtime.c                    │
│    ↓ GCC (compiler)                 │
│ *.o (object files)                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ All .o files + linker.ld            │
│    ↓ LD (linker)                    │
│ kernel.bin                          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ boot.bin + kernel.bin               │
│    ↓ cat (concatenate)              │
│ minios.img                          │
└─────────────────────────────────────┘
    ↓
Run in QEMU
```
