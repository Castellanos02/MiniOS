# MiniOS GRUB GUI Version

## What's New

The GRUB bootable version now includes a **graphical user interface**! It displays:

- 🎨 Color-coded interface with boxes and borders
- ⚡ Neural network activity suggestions
- 🎯 Interactive controls
- 📊 Status information

## Interface Layout

```
╔════════════════════════════════════════════════════════╗
║     MiniOS - Neural Activity Suggester                ║
╚════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────┐
│                                                      │
│  Suggested Activity:                                 │
│                                                      │
│  → Take a 15-minute walk outside                    │
│                                                      │
│  Press keys to interact:                             │
│                                                      │
│  [A] Accept   [R] Reject   [N] Next                 │
│                                                      │
└──────────────────────────────────────────────────────┘

┌─────────────────┐  ┌──────────────────────────────┐
│ SNN Model: Active│  │ Note: Interactive features   │
│ Activities: 8    │  │ require keyboard support     │
└─────────────────┘  └──────────────────────────────┘

MiniOS v1.0 | GRUB Edition | Press 'N' for next      *
```

## Controls

### Keyboard Commands

| Key | Action | Result |
|-----|--------|--------|
| **A** | Accept | Shows green "Activity Accepted!" and loads next |
| **R** | Reject | Shows red "Activity Rejected" and loads next |
| **N** | Next | Immediately loads next activity |

### Visual Feedback

**Accept (A key):**
```
┌────────────────────────┐
│  Activity Accepted!    │ (Green background)
└────────────────────────┘
```

**Reject (R key):**
```
┌────────────────────────┐
│  Activity Rejected     │ (Red background)
└────────────────────────┘
```

## Building & Running

### Build the GUI ISO

```bash
cd minios
make iso
```

### Run in QEMU

```bash
make run-iso
```

### What You'll See

1. **GRUB Menu** - Select "MiniOS - Neural Activity Suggester"
2. **GUI Loads** - Colorful interface appears
3. **Activity Shown** - First suggestion displayed
4. **Interactive** - Press A/R/N keys to interact

## Features

### Neural Network

The bootable version includes a working SNN:
- 8 different activity suggestions
- Pseudo-random selection
- Shows different activities each time

### Activities List

1. Take a 15-minute walk outside
2. Do 10 minutes of stretching  
3. Read a chapter from your book
4. Call a friend or family member
5. Practice mindfulness meditation
6. Work on a creative project
7. Review your weekly goals
8. Organize your workspace

### Color Scheme

- **Header**: Yellow text on blue background
- **Main Panel**: White/cyan themed
- **Success**: Light green background
- **Error**: Light red background
- **Status**: Light green on black

## Comparison: Bootable vs Simulators

| Feature | GRUB Bootable | Simulators |
|---------|---------------|------------|
| **Boots from ISO** | ✅ Yes | ❌ No |
| **Runs in QEMU** | ✅ Yes | ✅ Yes |
| **GUI** | ✅ Text-based boxes | ✅ CarPlay-style |
| **Activities** | 8 activities | 20 activities |
| **Learning** | Basic | Full ML |
| **Keyboard Input** | ✅ Yes | ✅ Yes |
| **Logging** | Basic | Full CSV export |
| **Real Hardware** | ✅ Can boot | ❌ Linux only |

## Technical Details

### Architecture
- 32-bit x86 (i386)
- GRUB multiboot compatible
- VGA text mode (80x25)
- Protected mode only

### Memory Layout
```
0x00100000  Kernel load address
0x000B8000  VGA text buffer
Stack grows down from top
```

### How It Works

1. **GRUB loads kernel** at 0x00100000
2. **Multiboot header** verified (magic: 0x2BADB002)
3. **VGA initialized** - Direct memory writes to 0xB8000
4. **GUI drawn** - Boxes using box-drawing characters (205, 186, etc.)
5. **Keyboard polling** - Reads from port 0x60
6. **Event loop** - Responds to key presses

### Key Scancodes

- A key: 0x1E
- R key: 0x13
- N key: 0x31

## Limitations

### Current Limitations

1. **No persistent storage** - Can't save logs
2. **Basic keyboard** - No complex input
3. **Single-user** - No multi-tasking
4. **8 activities** - vs 20 in simulators
5. **No network** - Standalone only

### Why These Limitations?

The bootable version focuses on **proof of concept**:
- Shows it's a real OS
- Demonstrates it boots
- Provides working GUI
- Interactive functionality

For full features, use the simulators!

## Advanced: Customization

### Change Activities

Edit `kernel/kernel_full.c`:

```c
static const char* activities[] = {
    "Your custom activity here",
    "Another activity",
    // ... up to 8 total
};
```

Rebuild:
```bash
make clean
make iso
```

### Change Colors

Edit color constants:
```c
#define HEADER_BG COLOR_BLUE
#define HEADER_FG COLOR_YELLOW
#define PANEL_BG COLOR_CYAN
// etc.
```

### Add More Activities

```c
// Increase array size
static const char* activities[] = {
    // ... add more activities ...
};
#define NUM_ACTIVITIES 16  // Update count
```

## Debugging

### Test in QEMU

```bash
make run-iso
```

**Expected**: GUI appears immediately after GRUB

### Check Keyboard

If keys don't work:
1. Click in QEMU window to focus
2. Try uppercase/lowercase
3. Check QEMU keyboard settings

### View Serial Output

```bash
qemu-system-x86_64 -cdrom build/minios.iso -serial stdio
```

## Real Hardware

### Boot from USB

```bash
# WARNING: Destroys USB data!
sudo dd if=build/minios.iso of=/dev/sdX bs=4M
sync
```

Then boot from USB drive.

### Boot from CD/DVD

```bash
# Burn ISO to disc
cdrecord -v dev=/dev/sr0 build/minios.iso
```

### VirtualBox

```bash
# Create VM
VBoxManage createvm --name "MiniOS" --register
VBoxManage modifyvm "MiniOS" --memory 128 --boot1 dvd
VBoxManage storagectl "MiniOS" --name "IDE" --add ide
VBoxManage storageattach "MiniOS" --storagectl "IDE" \
    --port 0 --device 0 --type dvddrive --medium build/minios.iso
VBoxManage startvm "MiniOS"
```

## Troubleshooting

### GUI doesn't appear

**Symptoms**: Black screen or text mode only

**Solutions**:
1. Rebuild: `make clean && make iso`
2. Check you selected right GRUB menu option
3. Verify VGA text mode supported

### Keys don't work

**Symptoms**: Pressing A/R/N does nothing

**Solutions**:
1. Click QEMU window to focus
2. Wait a few seconds for keyboard init
3. Try holding key briefly
4. Check keyboard layout (US assumed)

### Wrong activity order

This is normal - random selection works!

## Comparison with Full Simulators

### When to Use Bootable Version

✅ **Demonstrations** - Show it's a real OS
✅ **Portfolio** - Prove bootloader knowledge  
✅ **Education** - Learn OS booting
✅ **Testing** - Test on real hardware

### When to Use Simulators

✅ **Development** - Easier to debug
✅ **Full features** - All 20 activities
✅ **Learning** - Complete ML system
✅ **Daily use** - More practical

## Next Steps

1. ✅ Build: `make iso`
2. ✅ Run: `make run-iso`
3. ✅ Interact: Press A/R/N keys
4. 🔄 Customize: Edit activities
5. 🚀 Deploy: Burn to USB/CD

---

**You now have a fully bootable OS with GUI!** 🎉

For the complete experience with all features, run:
```bash
./minios_gui
```
