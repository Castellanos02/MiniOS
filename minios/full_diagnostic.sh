#!/bin/bash
# full_diagnostic.sh - Complete diagnostic of your MiniOS build

echo "=========================================="
echo "MiniOS Complete Diagnostic"
echo "=========================================="
echo ""

# 1. Environment
echo "1. ENVIRONMENT"
echo "----------------------------------------"
echo "Current directory: $(pwd)"
echo "User: $USER"
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo ""

# 2. Tools
echo "2. REQUIRED TOOLS"
echo "----------------------------------------"
for tool in nasm gcc ld grub-mkrescue xorriso qemu-system-x86_64; do
    if command -v $tool &> /dev/null; then
        echo "✓ $tool: $(which $tool)"
        if [ "$tool" == "qemu-system-x86_64" ]; then
            $tool --version | head -1
        fi
    else
        echo "✗ $tool: NOT FOUND"
    fi
done
echo ""

# 3. Build directory
echo "3. BUILD DIRECTORY"
echo "----------------------------------------"
if [ -d "build" ]; then
    echo "✓ build/ exists"
    echo "Contents:"
    ls -lh build/ | head -20
else
    echo "✗ build/ missing"
fi
echo ""

# 4. ISO file
echo "4. ISO FILE"
echo "----------------------------------------"
if [ -f "build/minios.iso" ]; then
    echo "✓ build/minios.iso exists"
    ls -lh build/minios.iso
    echo ""
    echo "File type:"
    file build/minios.iso
    echo ""
    echo "First 512 bytes (boot sector):"
    hexdump -C build/minios.iso | head -15
    echo ""
    echo "Boot signature check:"
    SIG=$(hexdump -s 510 -n 2 -e '2/1 "%02x"' build/minios.iso)
    if [ "$SIG" == "55aa" ]; then
        echo "✓ Boot signature present (0x55AA)"
    else
        echo "✗ Boot signature missing! Got: 0x$SIG"
    fi
else
    echo "✗ build/minios.iso MISSING"
    echo ""
    echo "This is the problem! Run: make iso"
fi
echo ""

# 5. ISO structure
echo "5. ISO DIRECTORY STRUCTURE"
echo "----------------------------------------"
if [ -d "build/isodir" ]; then
    echo "✓ build/isodir exists"
    echo ""
    echo "Structure:"
    find build/isodir -type f -o -type d | head -20
    echo ""
    if [ -f "build/isodir/boot/minios.bin" ]; then
        echo "✓ Kernel at build/isodir/boot/minios.bin"
        ls -lh build/isodir/boot/minios.bin
    else
        echo "✗ Kernel missing from ISO!"
    fi
    echo ""
    if [ -f "build/isodir/boot/grub/grub.cfg" ]; then
        echo "✓ GRUB config exists"
        echo "Contents:"
        cat build/isodir/boot/grub/grub.cfg
    else
        echo "✗ GRUB config missing!"
    fi
else
    echo "✗ build/isodir missing"
fi
echo ""

# 6. Kernel binary
echo "6. KERNEL BINARY"
echo "----------------------------------------"
if [ -f "build/minios.bin" ]; then
    echo "✓ build/minios.bin exists"
    ls -lh build/minios.bin
    echo ""
    echo "File type:"
    file build/minios.bin
    echo ""
    echo "ELF header:"
    readelf -h build/minios.bin 2>/dev/null | head -15 || echo "(readelf not available)"
else
    echo "✗ build/minios.bin missing"
fi
echo ""

# 7. Test QEMU command
echo "7. QEMU TEST"
echo "----------------------------------------"
echo "Testing QEMU with your ISO..."
echo ""

if [ -f "build/minios.iso" ]; then
    ISO_ABS="$(pwd)/build/minios.iso"
    echo "ISO absolute path: $ISO_ABS"
    echo ""
    echo "Command that will be executed:"
    echo "qemu-system-x86_64 -cdrom \"$ISO_ABS\" -m 128M -boot d"
    echo ""
    echo "Press Enter to start QEMU (or Ctrl+C to cancel)..."
    read
    
    qemu-system-x86_64 -cdrom "$ISO_ABS" -m 128M -boot d
    
    QEMU_EXIT=$?
    echo ""
    echo "QEMU exited with code: $QEMU_EXIT"
else
    echo "Cannot test - ISO doesn't exist"
fi

echo ""
echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="
echo ""

# Summary
if [ -f "build/minios.iso" ] && [ "$SIG" == "55aa" ] && [ -f "build/isodir/boot/minios.bin" ]; then
    echo "✓ Everything looks correct!"
    echo ""
    echo "If QEMU still fails to boot, try:"
    echo "  1. ./direct_run.sh"
    echo "  2. Different QEMU version"
    echo "  3. VirtualBox instead"
    echo "  4. Use the simulators: ./minios_gui"
else
    echo "✗ Issues found!"
    echo ""
    echo "To fix:"
    echo "  make clean"
    echo "  make iso"
    echo "  ./full_diagnostic.sh"
fi
