# MiniOS Troubleshooting Guide

## Issue: Simulator Stuck / Not Responding to Input

### Problem
The simulator displays but doesn't respond to keyboard input (A, R, I, L, Q keys don't work).

### Solution 1: Recompile (RECOMMENDED)
```bash
cd minios
gcc -o minios_simulator minios_simulator.c -lm
./minios_simulator
```

The latest version includes fixed keyboard input handling with proper terminal configuration.

### Solution 2: Use Test Script
```bash
cd minios
./test_minios.sh
```

This script checks your environment and launches the simulator with proper settings.

### Solution 3: Manual Terminal Reset
If the simulator exits abnormally:
```bash
reset
stty sane
```

## Issue: Display Issues / Garbled Text

### Cause
Terminal doesn't support ANSI color codes or has wrong settings.

### Solution
```bash
export TERM=xterm-256color
./minios_simulator
```

## Issue: "Permission Denied"

### Cause
Simulator not executable.

### Solution
```bash
chmod +x minios_simulator
./minios_simulator
```

## Issue: Compilation Errors

### Missing math library
```bash
# Add -lm flag
gcc -o minios_simulator minios_simulator.c -lm
```

### Missing headers
```bash
# Install build essentials
sudo apt-get install build-essential
```

## How Input Should Work

The simulator uses **non-blocking terminal input**:
- Terminal is set to raw mode (no line buffering)
- Uses `select()` to wait for input with 100ms timeout
- Reads single character at a time
- Processes immediately without Enter key

### Expected Behavior
1. Start simulator: `./minios_simulator`
2. See the UI with activity suggestion
3. Press **A** (no Enter needed) → Activity accepted, new suggestion appears
4. Press **R** (no Enter needed) → Activity rejected, new suggestion appears
5. Press **Q** (no Enter needed) → Simulator exits cleanly

### What to Check
1. **Are you in the right directory?**
   ```bash
   ls minios_simulator  # Should exist
   ```

2. **Is it the latest version?**
   ```bash
   ls -lh minios_simulator
   # If smaller than 25KB, recompile
   gcc -o minios_simulator minios_simulator.c -lm
   ```

3. **Terminal test**
   ```bash
   # Test if terminal accepts raw input
   stty -a | grep -i echo
   # Should show terminal settings
   ```

## Issue: Can't Export Logs

### Problem
Pressing 'E' in log view doesn't create CSV file.

### Solution
```bash
# Create outputs directory if missing
mkdir -p /mnt/user-data/outputs

# Run simulator
./minios_simulator

# Press L, then E to export
# File will be at: /mnt/user-data/outputs/minios_feedback_logs.csv
```

## Issue: Simulator Exits Immediately

### Cause
Terminal not compatible or missing library.

### Debug
```bash
# Run with error output
./minios_simulator 2>&1 | tee error.log

# Check the log
cat error.log
```

## Technical Details

### Terminal Configuration Used
```c
struct termios raw;
raw.c_lflag &= ~(ECHO | ICANON | ISIG);  // Disable echo, canonical mode, signals
raw.c_iflag &= ~(IXON | ICRNL);           // Disable flow control, CR to NL
raw.c_cc[VMIN] = 0;                       // Non-blocking
raw.c_cc[VTIME] = 1;                      // 100ms timeout
```

### Input Reading Method
```c
fd_set readfds;
struct timeval timeout;
FD_ZERO(&readfds);
FD_SET(STDIN_FILENO, &readfds);
timeout.tv_sec = 0;
timeout.tv_usec = 100000; // 100ms

int ready = select(STDIN_FILENO + 1, &readfds, NULL, NULL, &timeout);
if (ready > 0) {
    char c = getchar();
    // Process c immediately
}
```

## Still Not Working?

### Alternative: Non-interactive Mode
If terminal input is completely broken, you could modify the code to use a simpler input method:

```c
// Replace the main loop with:
while (1) {
    draw_ui();
    printf("\nEnter command (a/r/i/l/q): ");
    char cmd[10];
    if (fgets(cmd, sizeof(cmd), stdin)) {
        char c = cmd[0];
        // ... process c ...
    }
}
```

### Contact Information
This is an educational project. If issues persist:
1. Check terminal compatibility (should support ANSI)
2. Try different terminal emulators (gnome-terminal, xterm, konsole)
3. Verify system has libm (math library)

## Quick Reference

### File Locations
- Simulator: `./minios_simulator`
- Source: `./minios_simulator.c`
- Test script: `./test_minios.sh`
- Logs: `/mnt/user-data/outputs/minios_feedback_logs.csv`

### Compilation
```bash
gcc -o minios_simulator minios_simulator.c -lm -Wall
```

### Running
```bash
# Direct
./minios_simulator

# With test script
./test_minios.sh

# Check version
ls -lh minios_simulator
# Should be ~26-28 KB
```

### Emergency Exit
If simulator hangs:
- Press **Ctrl+C** to force quit
- Run `reset` to restore terminal
- Run `stty sane` to fix terminal settings

---

**Last Updated:** 2026-02-16  
**Applies to:** MiniOS v1.0 (Fixed Input Version)
