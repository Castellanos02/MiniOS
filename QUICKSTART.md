# MiniOS Quick Start Guide

## What is MiniOS?

MiniOS is a custom operating system with an embedded Spiking Neural Network (SNN) that provides intelligent activity suggestions based on calendar context. It demonstrates OS development concepts including:

- Custom bootloader and kernel
- Hardware interrupt handling
- Memory management
- GUI framework
- Machine learning integration
- Real-time performance monitoring

## Two Versions Available

### 1. Full OS (Requires QEMU)
The complete OS that boots from scratch with custom bootloader and kernel.

**Requirements:**
- NASM assembler
- GCC compiler
- QEMU x86_64 emulator

**Build & Run:**
```bash
cd minios
make
make run
```

### 2. Simulator (Ready to Run!)
A Linux user-space simulation that demonstrates all OS features without requiring QEMU.

**Run Now:**
```bash
cd minios
./minios_simulator
```

## How to Use

### Interface Overview

```
═══════════════════════════════════════════════════════════
          MiniOS - Neural Activity Suggester
═══════════════════════════════════════════════════════════

  Current Time: 10:30:00, Monday 16, 2026
  Day of Week: Monday

  Suggested Activity:
  → Take a 15-minute walk outside

  Performance Metrics:
  • Inference Latency: 15 ms
  • Model Accuracy: 73.2% (last 100 interactions)
  • Total Feedback: 42 interactions

  Actions:
  [A] Accept  [R] Reject  [I] Ignore  [L] View Logs  [Q] Quit

───────────────────────────────────────────────────────────
 CPU: 12.3%  |  Memory: 2.45 MB  |  Uptime: 127 s  |  Logs: 42/1000
───────────────────────────────────────────────────────────
```

### Controls

- **A** - Accept the suggested activity
  - Increases the score for this activity
  - System learns you like this type of suggestion
  - Generates a new suggestion

- **R** - Reject the suggested activity
  - Decreases the score for this activity
  - System learns to avoid similar suggestions
  - Generates a new suggestion

- **I** - Ignore the suggestion
  - Neutral response, no learning applied
  - Logs the interaction for statistics
  - Current suggestion remains

- **L** - View detailed logs
  - Shows last 20 interactions
  - Displays statistics (accuracy, avg latency)
  - Option to export logs to CSV

- **Q** - Quit the application

## How the SNN Works

### Neural Network Architecture

```
Input Layer (10 neurons)
    ↓ Calendar Context Features
Hidden Layer (10 neurons)
    ↓ Sigmoid Activation
Activity Scores (20 activities)
    ↓ Softmax Selection
Suggested Activity
```

### Features Extracted from Calendar

- Hour of day
- Day of week
- Month of year
- Time of day category (morning/afternoon/evening)
- Workday vs weekend
- Hash-based contextual features

### Learning Algorithm

1. **Initial Prediction**: Neural network forward pass
2. **Score Adjustment**: Based on user feedback
   ```
   if accept:  score += 0.1
   if reject:  score -= 0.1
   if ignore:  no change
   ```
3. **Temporal Weighting**: Recent feedback weighted more heavily
4. **Exploration**: 20% random suggestions to discover preferences

### Activity Categories

The system suggests 20 different activities across categories:

1. **Physical**: Walking, stretching, workouts
2. **Mental**: Reading, learning, podcasts
3. **Social**: Calling friends, family time
4. **Productive**: Organizing, planning, emails
5. **Creative**: Projects, hobbies, journaling
6. **Wellness**: Healthy snacks, meditation, rest

## Performance Metrics Explained

### CPU Usage
Percentage of CPU time used by the application. Typical values:
- Idle: 5-15%
- Active (inference): 20-40%
- High load: 40-60%

### Memory Usage
RAM consumed by the application:
- Baseline: ~2-3 MB
- With logs: Grows by ~200 bytes per interaction
- Maximum: ~5 MB (1000 logs)

### Inference Latency
Time to generate a suggestion:
- Typical: 10-30 ms
- Good: < 50 ms
- Slow: > 100 ms

Factors affecting latency:
- Model complexity
- Number of historical logs
- System load

### Model Accuracy
Percentage of accepted suggestions (last 100 interactions):
- Learning: 40-60%
- Trained: 60-80%
- Well-trained: 80-95%

## Logging System

### Log Entry Format
```csv
Timestamp,Activity,Feedback,CPU_Usage,Memory_Used_MB,Latency_ms
1708088400,Take a walk outside,accept,12.3,2.45,15
```

### Exported Log File
- Location: `/mnt/user-data/outputs/minios_feedback_logs.csv`
- Format: CSV (comma-separated values)
- Fields: Timestamp, Activity, Feedback, CPU, Memory, Latency
- Use: Import into Excel, Python, R for analysis

### Analysis Ideas

1. **Activity Patterns**
   - Which activities are most accepted?
   - Time-of-day preferences?
   - Weekend vs weekday patterns?

2. **Learning Curve**
   - How does accuracy improve over time?
   - How many interactions until trained?

3. **Performance Analysis**
   - Correlation between log count and latency?
   - Memory usage growth rate?

## Tips for Best Results

### Training the Model

1. **Start Fresh**: Give honest feedback for first 20-30 interactions
2. **Be Consistent**: Similar situations should get similar feedback
3. **Variety**: Try accepting different types of activities
4. **Patience**: Model improves after 50-100 interactions

### Getting Good Suggestions

- Accept activities you actually want to do
- Reject activities that don't fit the context
- Use "ignore" for borderline suggestions
- The model learns your patterns over time

### Experimenting

Try these scenarios:
1. Accept only physical activities → Model suggests more exercise
2. Reject all social activities → Model learns you prefer solo tasks
3. Ignore everything → Model maintains diverse suggestions
4. Random feedback → Model struggles to learn (low accuracy)

## Troubleshooting

### Simulator won't start
```bash
# Check if file is executable
chmod +x minios_simulator
./minios_simulator
```

### Terminal display issues
```bash
# Reset terminal
reset
./minios_simulator
```

### Can't see cursor
- This is normal - raw mode is enabled
- Press Q to exit and terminal returns to normal

### Export fails
```bash
# Ensure outputs directory exists
mkdir -p /mnt/user-data/outputs
./minios_simulator
```

## Advanced: Building the Full OS

### Install Dependencies
```bash
sudo apt-get update
sudo apt-get install -y nasm gcc qemu-system-x86
```

### Build Process
```bash
cd minios
make clean
make
```

This creates:
- `build/boot.bin` - Bootloader (512 bytes)
- `build/kernel.bin` - Kernel binary
- `build/minios.img` - Full OS image (1MB)

### Run in QEMU
```bash
make run
```

### Debug Mode
```bash
# Terminal 1
make debug

# Terminal 2
gdb
(gdb) target remote :1234
(gdb) break kernel_main
(gdb) continue
```

## Source Code Structure

```
minios/
├── boot/
│   └── boot.asm              # Bootloader (x86_64 assembly)
├── kernel/
│   ├── kernel_main.c         # Kernel entry point
│   ├── interrupts.asm        # Interrupt handlers
│   └── linker.ld             # Linker script
├── gui/
│   └── gui.c                 # GUI framework
├── python/
│   └── python_runtime.c      # SNN model
├── minios_simulator.c        # Linux simulator
├── Makefile                  # Build system
└── README.md                 # Documentation
```

## Learning Resources

### OS Development
- [OSDev Wiki](https://wiki.osdev.org/)
- [Writing a Simple Operating System from Scratch](https://www.cs.bham.ac.uk/~exr/lectures/opsys/10_11/lectures/os-dev.pdf)

### Neural Networks
- [Neural Networks and Deep Learning](http://neuralnetworksanddeeplearning.com/)
- [Spiking Neural Networks](https://en.wikipedia.org/wiki/Spiking_neural_network)

### x86_64 Architecture
- [Intel 64 and IA-32 Architectures Software Developer Manuals](https://software.intel.com/content/www/us/en/develop/articles/intel-sdm.html)

## Next Steps

1. **Try the Simulator**: Run `./minios_simulator` now!
2. **Interact 50+ Times**: Train the model with honest feedback
3. **Export Logs**: Analyze your usage patterns
4. **Modify Code**: Try changing activities or learning rate
5. **Build Full OS**: Install QEMU and build the real OS

## Support

This is an educational project demonstrating:
- Operating system fundamentals
- Machine learning integration
- Real-time systems
- User interface design
- Performance monitoring

Have fun exploring!
