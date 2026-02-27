# MiniOS GRUB Edition - Setup Guide

## What Changed?

MiniOS now uses **GRUB multiboot** instead of a custom bootloader. This means:

✅ **Reliable booting** - GRUB is tested on thousands of systems
✅ **No boot hangs** - GRUB handles all the hardware complexity  
✅ **Easy to build** - Simpler build process
✅ **Industry standard** - What Linux and professional OS projects use

## Quick Start

### Step 1: Install GRUB Tools

```bash
# Ubuntu/Debian
sudo apt-get install grub-pc-bin xorriso mtools

# Fedora/RHEL
sudo dnf install grub2-pc xorriso mtools

# Arch Linux
sudo pacman -S grub xorriso mtools
```

### Step 2: Build the ISO

```bash
cd minios
make iso
```

This creates `build/minios.iso` - a bootable ISO file!

### Step 3: Run in QEMU

```bash
make run-iso
```

QEMU will boot from the ISO and you'll see MiniOS running!

## What You'll See

When you run `make run-iso`, QEMU will show:

```
GRUB Menu
─────────────────────────────────────
  MiniOS - Neural Activity Suggester
  MiniOS - Safe Mode

Press Enter to boot
```

Then after selecting the first option:

```
========================================
       MiniOS v1.0 - GRUB Edition
========================================

Boot Status:
  [OK] Multiboot header verified
  [OK] Kernel loaded successfully
  [OK] VGA text mode initialized
  [OK] Protected mode active

System Information:
  Architecture: x86 (32-bit)
  Bootloader: GRUB
  Display: VGA Text Mode (80x25)

MiniOS Features:
  * Neural Activity Suggester
  * Spiking Neural Network
  * Performance Monitoring
  * Feedback Learning System

Note: Full GUI requires simulators
Run './minios_gui' for complete experience

Kernel initialization complete!
System is running...
```

## How It Works

### Multiboot Specification

GRUB uses the **Multiboot** specification:

1. **Multiboot Header**: Special signature at start of kernel
   ```
   Magic: 0x1BADB002
   Flags: Page align + Memory info
   Checksum: -(magic + flags)
   ```

2. **GRUB loads kernel**: Reads the multiboot header
3. **Sets up environment**: Enters 32-bit protected mode
4. **Jumps to kernel**: Calls `_start` function

### Build Process

```
multiboot_header.asm  →  NASM  →  multiboot_header.o
                                         ↓
kernel_simple.c  →  GCC -m32  →  kernel_simple.o
                                         ↓
                            LD (32-bit) → minios.bin
                                         ↓
                        Copy to ISO structure
                                         ↓
                    grub-mkrescue  →  minios.iso
```

### ISO Structure

```
minios.iso
├── boot/
│   ├── grub/
│   │   ├── grub.cfg          # GRUB menu configuration
│   │   └── i386-pc/          # GRUB bootloader files
│   └── minios.bin            # Your kernel
```

## Customizing GRUB

### Edit Boot Menu

Edit `grub.cfg`:

```
set timeout=3
set default=0

menuentry "MiniOS - My Custom Name" {
    multiboot /boot/minios.bin
    boot
}

menuentry "MiniOS - Debug Mode" {
    multiboot /boot/minios.bin --debug
    boot
}
```

Then rebuild:
```bash
make iso
```

### Change Timeout

```
set timeout=10    # Wait 10 seconds
set timeout=0     # Boot immediately
set timeout=-1    # Wait forever
```

### Add More Kernels

```
menuentry "MiniOS v1.0" {
    multiboot /boot/minios.bin
    boot
}

menuentry "MiniOS v2.0" {
    multiboot /boot/minios_v2.bin
    boot
}
```

## Testing Without QEMU

### VirtualBox

```bash
# Import ISO into VirtualBox
VBoxManage createvm --name "MiniOS" --register
VBoxManage modifyvm "MiniOS" --memory 128 --boot1 dvd
VBoxManage storagectl "MiniOS" --name "IDE" --add ide
VBoxManage storageattach "MiniOS" --storagectl "IDE" \
    --port 0 --device 0 --type dvddrive --medium build/minios.iso
VBoxManage startvm "MiniOS"
```

### Real Hardware (USB Boot)

```bash
# Write ISO to USB drive (WARNING: Destroys USB data!)
sudo dd if=build/minios.iso of=/dev/sdX bs=4M status=progress
sync

# Boot from USB on real computer
```

**Warning**: Only do this if you know what you're doing!

## Expanding the Kernel

### Current Limitations

The GRUB version currently shows a simple boot message. To add full functionality:

### Option 1: Use the Simulators (Recommended)

The simulators have ALL features working:
```bash
./minios_gui        # Full GUI, all features
./minios_simulator  # Full text interface
```

### Option 2: Port Features to 32-bit Kernel

To add features to the bootable version:

1. **Port C code to 32-bit**:
   - Change from 64-bit to 32-bit types
   - Adapt memory addresses
   - Recompile with `-m32`

2. **Add interrupt handling**:
   - Set up IDT (Interrupt Descriptor Table)
   - Add keyboard handler
   - Add timer handler

3. **Add GUI code**:
   - Port `gui.c` to 32-bit
   - Keep VGA text mode

4. **Add SNN model**:
   - Port `python_runtime.c` to 32-bit
   - Link all together

This is a lot of work! The simulators are much easier.

## Troubleshooting

### "grub-mkrescue: command not found"

```bash
sudo apt-get install grub-pc-bin xorriso
```

### "xorriso: command not found"

```bash
sudo apt-get install xorriso
```

### ISO boots to GRUB prompt instead of menu

Your `grub.cfg` has syntax errors. Check:
- Correct braces: `{ }`
- Each command on new line
- Proper menuentry format

### QEMU shows "No bootable device"

The ISO wasn't created properly:
```bash
make clean
make iso
```

### Want to test on real hardware

```bash
# Burn to CD/DVD
cdrecord -v dev=/dev/sr0 build/minios.iso

# Or write to USB (DANGER: destroys USB data!)
sudo dd if=build/minios.iso of=/dev/sdX bs=4M
```

## Advantages of GRUB

### vs Custom Bootloader

| Feature | GRUB | Custom Bootloader |
|---------|------|-------------------|
| Reliability | ⭐⭐⭐⭐⭐ Very reliable | ⭐⭐ Often has issues |
| Setup | ⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐⭐ Complex |
| Hardware support | ⭐⭐⭐⭐⭐ Extensive | ⭐⭐ Limited |
| Debugging | ⭐⭐⭐⭐⭐ Good tools | ⭐⭐ Difficult |
| Professional use | ✅ Yes | ❌ Rarely |

### Features GRUB Provides

- Multiple boot options
- Command line interface
- Filesystem drivers (ext2/3/4, FAT, etc.)
- Network boot (PXE)
- Memory testing
- Hardware detection
- Error recovery

## Advanced: Multiboot2

For even more features, use Multiboot2:

```asm
; Multiboot2 header
MULTIBOOT2_MAGIC equ 0xE85250D6

section .multiboot
align 8
multiboot_start:
    dd MULTIBOOT2_MAGIC
    dd 0  ; Architecture: i386
    dd multiboot_end - multiboot_start
    dd -(MULTIBOOT2_MAGIC + 0 + (multiboot_end - multiboot_start))
    
    ; End tag
    dw 0, 0
    dd 8
multiboot_end:
```

Multiboot2 provides:
- Better memory map
- More boot info
- Module loading
- Framebuffer info

## Files in This Build

```
minios/
├── kernel/
│   ├── multiboot_header.asm    # Multiboot magic
│   ├── kernel_simple.c         # 32-bit kernel
│   └── linker_multiboot.ld     # Linker script
├── grub.cfg                    # GRUB menu
├── Makefile                    # Build system
└── build/
    ├── minios.bin              # Kernel binary
    ├── minios.iso              # Bootable ISO
    └── isodir/                 # ISO structure
        └── boot/
            ├── grub/
            │   └── grub.cfg
            └── minios.bin
```

## Comparison: GRUB vs Custom vs Simulators

| Aspect | GRUB ISO | Custom Bootloader | Simulators |
|--------|----------|-------------------|------------|
| Bootability | ✅ Yes | ⚠️ Has issues | ❌ No |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Full features | ⚠️ Need porting | ⚠️ Need porting | ✅ All work |
| Development speed | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| Debugging | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Professional | ✅ Yes | ❌ No | ✅ Yes |

## Recommendation

**For demonstration**: Use the GRUB ISO - shows it boots!
**For development**: Use the simulators - all features work!
**For learning**: Study the GRUB setup - industry standard!

## Next Steps

1. ✅ **Build ISO**: `make iso`
2. ✅ **Test boot**: `make run-iso`
3. ✅ **Show others**: Share the ISO file
4. 🔄 **Add features**: Port code from simulators (optional)
5. ⭐ **Use simulators**: Run `./minios_gui` for full experience

---

**You now have a bootable OS using industry-standard GRUB!** 🎉

The ISO file can boot on:
- QEMU/KVM
- VirtualBox
- VMware
- Real hardware (with caution)

For full functionality, use the simulators which have everything working perfectly!
