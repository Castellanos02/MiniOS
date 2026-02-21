#!/bin/bash
# diagnose.sh - Check MiniOS build status

echo "======================================"
echo "MiniOS Build Diagnostics"
echo "======================================"
echo ""

# Check tools
echo "1. Checking required tools..."
echo ""

check_tool() {
    if command -v $1 &> /dev/null; then
        echo "  ✓ $1: $(which $1)"
    else
        echo "  ✗ $1: NOT FOUND"
        return 1
    fi
}

MISSING=0
check_tool nasm || MISSING=1
check_tool gcc || MISSING=1
check_tool ld || MISSING=1
check_tool grub-mkrescue || MISSING=1
check_tool xorriso || MISSING=1
check_tool qemu-system-x86_64 || MISSING=1

echo ""

if [ $MISSING -eq 1 ]; then
    echo "❌ Missing tools detected!"
    echo ""
    echo "Install with:"
    echo "  sudo apt-get install nasm gcc binutils grub-pc-bin xorriso mtools qemu-system-x86"
    echo ""
    exit 1
fi

# Check build directory
echo "2. Checking build directory..."
echo ""

if [ ! -d "build" ]; then
    echo "  ✗ build/ directory does not exist"
    echo "  Run: mkdir -p build"
else
    echo "  ✓ build/ directory exists"
fi

echo ""

# Check for ISO
echo "3. Checking for ISO file..."
echo ""

if [ ! -f "build/minios.iso" ]; then
    echo "  ✗ build/minios.iso NOT FOUND"
    echo "  This is why QEMU can't boot!"
    echo ""
    echo "  Solution: Run 'make iso' to build it"
    ISO_EXISTS=0
else
    echo "  ✓ build/minios.iso exists"
    echo "  Size: $(ls -lh build/minios.iso | awk '{print $5}')"
    
    # Check if it's a valid ISO
    FILE_TYPE=$(file build/minios.iso 2>/dev/null)
    if echo "$FILE_TYPE" | grep -q "ISO 9660\|DOS/MBR"; then
        echo "  ✓ Valid bootable ISO"
        ISO_EXISTS=1
    else
        echo "  ✗ Invalid ISO file"
        echo "  File type: $FILE_TYPE"
        ISO_EXISTS=0
    fi
fi

echo ""

# Check kernel binary
echo "4. Checking kernel binary..."
echo ""

if [ ! -f "build/minios.bin" ]; then
    echo "  ✗ build/minios.bin NOT FOUND"
    echo "  Run: make iso"
else
    echo "  ✓ build/minios.bin exists"
    echo "  Size: $(ls -lh build/minios.bin | awk '{print $5}')"
    
    FILE_TYPE=$(file build/minios.bin 2>/dev/null)
    if echo "$FILE_TYPE" | grep -q "ELF.*Intel"; then
        echo "  ✓ Valid ELF executable"
    else
        echo "  ⚠ Unexpected file type: $FILE_TYPE"
    fi
fi

echo ""

# Check ISO structure
if [ $ISO_EXISTS -eq 1 ]; then
    echo "5. Checking ISO structure..."
    echo ""
    
    if [ -d "build/isodir/boot" ]; then
        echo "  ✓ build/isodir/boot/ exists"
        
        if [ -f "build/isodir/boot/minios.bin" ]; then
            echo "  ✓ Kernel in ISO structure"
        else
            echo "  ✗ Kernel missing from ISO structure"
        fi
        
        if [ -f "build/isodir/boot/grub/grub.cfg" ]; then
            echo "  ✓ GRUB config exists"
        else
            echo "  ✗ GRUB config missing"
        fi
    else
        echo "  ✗ ISO directory structure missing"
    fi
    echo ""
fi

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [ $ISO_EXISTS -eq 1 ]; then
    echo "✓ ISO is ready!"
    echo ""
    echo "You can run:"
    echo "  make run-iso"
    echo ""
    echo "Or manually:"
    echo "  qemu-system-x86_64 -cdrom build/minios.iso -m 128M"
    echo ""
else
    echo "✗ ISO needs to be built"
    echo ""
    echo "Run these commands:"
    echo "  make clean"
    echo "  make iso"
    echo "  make run-iso"
    echo ""
    echo "Or use the automated script:"
    echo "  ./build_and_run.sh"
    echo ""
fi

echo "======================================"
