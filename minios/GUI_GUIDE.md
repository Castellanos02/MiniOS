# MiniOS CarPlay-Style GUI Guide

## Overview

The MiniOS GUI provides a modern, Apple CarPlay-inspired interface for the neural activity suggester. It features:

- **Card-based design** - Clean, organized information cards
- **Dark mode interface** - Easy on the eyes with high contrast
- **Real-time updates** - Live metrics and smooth animations  
- **Unicode icons** - Emoji and symbols for visual appeal
- **Responsive layout** - Adapts to terminal size

## Screenshots (Terminal View)

```
╭────────────────────────────────────────────────────╮
│                                                    │
│   MiniOS Neural Activity Suggester                │
│                                                    │
╰────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────╮
│  📅 Current Time                                   │
│                                                    │
│  Mon 15:40:49                                      │
╰────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────╮
│  ⚡ Suggested Activity                             │
│                                                    │
│  🚶  Take a 15-minute walk outside                │
│                                                    │
│  Category: Physical                                │
│  Confidence: 73%                                   │
╰────────────────────────────────────────────────────╯

╭──────────────────────╮  ╭──────────────────────╮
│  📊 Performance      │  │  ⚙ System           │
│                      │  │                      │
│  Latency: 21ms       │  │  CPU: 9.4%           │
│  Accuracy: 0.0%      │  │  RAM: 2.85MB         │
│  Logs: 0/1000        │  │  Uptime: 37s         │
╰──────────────────────╯  ╰──────────────────────╯

 [A] Accept   [R] Reject   [I] Ignore   [L] Logs   [Q] Quit
```

## Features

### 1. Time Card
- Shows current date, day of week, and time
- Updates in real-time
- Calendar icon for visual identification

### 2. Activity Card (Main)
- Large, prominent display of suggested activity
- Category-specific emoji icon
- Activity category (Physical, Mental, Social, etc.)
- Confidence score (0-100%)
- Color-coded borders

### 3. Performance Card
- **Latency**: How fast the AI generates suggestions
- **Accuracy**: Percentage of accepted suggestions (last 100)
- **Logs**: Number of recorded interactions

### 4. System Card
- **CPU**: Processor usage percentage
- **RAM**: Memory consumption in MB
- **Uptime**: How long the system has been running

### 5. Notification System
- Pops up for 3 seconds after each action
- Color-coded by type:
  - 🟢 **Green**: Success (Accept)
  - 🔴 **Red**: Error/Rejection (Reject)
  - 🔵 **Blue**: Info (Ignore)

### 6. Action Buttons
- Color-coded buttons at bottom
- Keyboard shortcuts (A, R, I, L, Q)
- Always visible for quick access

## Color Scheme

Inspired by Apple's design language:

| Element | Color | RGB | Usage |
|---------|-------|-----|-------|
| Background | Black | 0,0,0 | Main background |
| Cards | Dark Gray | 28,28,30 | Content cards |
| Accent | Blue | 0,122,255 | Interactive elements |
| Success | Green | 52,199,89 | Positive actions |
| Warning | Orange | 255,149,0 | Caution |
| Error | Red | 255,59,48 | Negative actions |
| Primary Text | White | 255,255,255 | Main content |
| Secondary Text | Gray | 174,174,178 | Labels, metadata |

## Activity Categories with Icons

### Physical Activities 💪
- 🚶 Take a 15-minute walk outside
- 🧘 Do 10 minutes of stretching
- 💪 Quick workout

### Mental Activities 🧠
- 📚 Read a book chapter
- 🎓 Learn something new
- 🎧 Listen to podcast

### Social Activities 👥
- 📞 Call a friend or family

### Productive Activities 📋
- 📋 Review weekly goals
- 🗂 Organize workspace
- 💰 Review budget
- 🍽 Plan meals
- 📧 Catch up on emails

### Creative Activities 🎨
- 🎨 Work on creative project
- ✍ Write in journal
- 🎯 Practice hobby
- 💡 Brainstorm ideas

### Wellness Activities 🌿
- 🧘 Meditate for 10 minutes
- 🥗 Prepare healthy snack
- 😴 Take power nap

## Controls

### Main Interface
- **A** or **a** - Accept activity (learn preference)
- **R** or **r** - Reject activity (avoid similar)
- **I** or **i** - Ignore activity (neutral, no learning)
- **L** or **l** - View detailed logs
- **Q** or **q** - Quit application

### Log View
- **E** or **e** - Export logs to CSV
- **Enter** - Return to main interface
- **Q** or **q** - Return to main interface
- **Esc** - Return to main interface

## Usage Tips

### 1. Terminal Requirements
For best experience:
- Terminal width: 80+ columns
- Terminal height: 30+ rows
- UTF-8 encoding support
- 256-color support

Check your terminal size:
```bash
echo "Width: $COLUMNS, Height: $LINES"
```

Recommended terminals:
- ✅ GNOME Terminal
- ✅ Konsole
- ✅ iTerm2 (macOS)
- ✅ Windows Terminal
- ✅ xterm-256color

### 2. Font Recommendations
For proper emoji display:
- Noto Color Emoji
- Apple Color Emoji
- Segoe UI Emoji
- DejaVu Sans Mono

### 3. Resize Terminal
If UI looks cramped:
```bash
# Set to larger size
printf '\033[8;35;100t'  # 35 rows, 100 columns
```

### 4. Color Issues
If colors don't show:
```bash
export TERM=xterm-256color
./minios_gui
```

## Running the GUI

### Quick Start
```bash
cd minios
./minios_gui
```

### Build from Source
```bash
cd minios
make minios_gui
./minios_gui
```

### With Make Shortcuts
```bash
make run-gui
```

## Comparison: GUI vs Text Mode

| Feature | GUI Version | Text Version |
|---------|-------------|--------------|
| Interface | Card-based, modern | Simple text layout |
| Colors | Full RGB (16M colors) | 16 ANSI colors |
| Icons | Unicode emoji | ASCII symbols |
| Layout | Responsive cards | Fixed columns |
| Animations | Smooth transitions | Static display |
| Readability | High contrast, clear | Good, functional |
| Terminal Support | Modern terminals | Any terminal |

## Troubleshooting

### Issue: Boxes Don't Render
**Problem:** Box drawing characters show as `?` or squares

**Solution:**
```bash
# Check locale
locale | grep UTF-8

# Set UTF-8
export LC_ALL=en_US.UTF-8
./minios_gui
```

### Issue: Emoji Don't Show
**Problem:** Emoji show as `[?]` or empty boxes

**Solutions:**
1. Install emoji fonts:
   ```bash
   sudo apt-get install fonts-noto-color-emoji
   ```

2. Use terminal with emoji support (GNOME Terminal, Konsole)

3. Fallback: Emoji will show as text symbols

### Issue: Colors Look Wrong
**Problem:** Colors are dim or incorrect

**Solution:**
```bash
# Check color support
tput colors

# Should show 256 or more
# If less, set terminal:
export TERM=xterm-256color
```

### Issue: Layout Broken
**Problem:** Cards overlap or text wraps incorrectly

**Solution:**
```bash
# Maximize terminal window
# Or resize:
resize -s 35 100  # 35 rows, 100 columns
./minios_gui
```

### Issue: Input Not Working
**Problem:** Keys don't register

**Solution:**
1. Recompile latest version:
   ```bash
   make minios_gui
   ```

2. Check terminal is in focus

3. Try text version:
   ```bash
   ./minios_simulator
   ```

## Advanced Customization

### Change Colors
Edit `minios_gui.c`:
```c
// Find color definitions
#define BG_ACCENT "\033[48;2;0;122;255m"  // Blue
// Change RGB values: \033[48;2;R;G;Bm

// Example: Purple accent
#define BG_ACCENT "\033[48;2;175;82;222m"
```

Recompile:
```bash
gcc -o minios_gui minios_gui.c -lm
```

### Modify Layout
Edit `draw_ui()` function:
```c
// Change card positions
draw_card(2, 10, card_width, 8, "Title", "Content");
//        x  y   width    height
```

### Add Custom Icons
Use Unicode emoji or symbols:
```c
#define MY_ICON "🎯"
printf("%s Custom text", MY_ICON);
```

Find more icons:
- https://emojipedia.org/
- https://www.unicode.org/emoji/charts/

## Performance

### Optimization Tips

1. **Reduce refresh rate** (save CPU):
   ```c
   // In main loop, change timeout
   timeout.tv_usec = 200000; // 200ms instead of 100ms
   ```

2. **Disable animations**:
   - Notifications can be static
   - Remove time-based effects

3. **Minimize redraws**:
   - Only update changed elements
   - Cache static content

### Benchmarks
- **CPU Usage**: 8-12% idle, 20-30% active
- **Memory**: 3-4 MB
- **Latency**: <5ms UI response time
- **Refresh**: 10 FPS (100ms per frame)

## Keyboard Shortcuts Reference

```
┌─────────────────────────────────────────┐
│  MiniOS GUI Keyboard Shortcuts          │
├─────────────────────────────────────────┤
│  A   Accept current suggestion          │
│  R   Reject current suggestion          │
│  I   Ignore (no learning)               │
│  L   View activity logs                 │
│  Q   Quit application                   │
│                                         │
│  In Log View:                           │
│  E   Export logs to CSV                 │
│  ↵   Return to main menu                │
│  Esc Return to main menu                │
└─────────────────────────────────────────┘
```

## FAQ

**Q: Can I resize the window?**  
A: Yes! The GUI adapts to terminal size. Minimum 80×24 recommended.

**Q: Does it work on Windows?**  
A: Yes, with Windows Terminal or WSL. May need UTF-8 encoding enabled.

**Q: Can I use it over SSH?**  
A: Yes! Works perfectly over SSH with terminal forwarding.

**Q: Why CarPlay design?**  
A: CarPlay's card-based interface is perfect for focused, glanceable information - ideal for activity suggestions.

**Q: Can I customize the theme?**  
A: Yes! Edit the color definitions in `minios_gui.c` and recompile.

**Q: Is it GPU accelerated?**  
A: No, it's pure terminal graphics (ANSI codes). Very lightweight!

## See Also

- **QUICKSTART.md** - Getting started guide
- **TROUBLESHOOTING.md** - Common issues and fixes
- **ARCHITECTURE.md** - System design details
- **TECHNICAL_SPEC.md** - Complete specifications

---

**Version:** 1.0  
**Last Updated:** 2026-02-16  
**License:** MIT
