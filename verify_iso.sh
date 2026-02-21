#!/bin/bash
# verify_iso.sh - Verify the ISO is properly bootable

echo "======================================"
echo "ISO Verification"
echo "======================================"
echo ""

if [ ! -f "build/minios.iso" ]; then
    echo "❌ ISO not found!"
    exit 1
fi

# Check file type
echo "1. File type:"
file build/minios.iso
echo ""

# Check size
echo "2. Size:"
ls -lh build/minios.iso
echo ""

# Check if it's readable
echo "3. Permissions:"
ls -la build/minios.iso
echo ""

# Try to read first 512 bytes (boot sector)
echo "4. Boot sector (first 512 bytes):"
hexdump -C build/minios.iso | head -20
echo ""

# Check for boot signature (0x55AA at end of boot sector)
echo "5. Boot signature check:"
SIGNATURE=$(dd if=build/minios.iso bs=1 skip=510 count=2 2>/dev/null | hexdump -v -e '/1 "%02x"')
if [ "$SIGNATURE" == "55aa" ]; then
    echo "✓ Boot signature found (0x55AA)"
else
    echo "✗ Boot signature NOT found! Got: 0x$SIGNATURE"
    echo "  This ISO may not be bootable"
fi
echo ""

# Check ISO structure
echo "6. ISO structure:"
if command -v isoinfo &> /dev/null; then
    echo "Root directory:"
    isoinfo -l -i build/minios.iso | head -30
else
    echo "(isoinfo not available - install with: sudo apt-get install genisoimage)"
fi
echo ""

# Check if kernel exists in ISO
echo "7. Looking for kernel in ISO structure:"
if [ -f "build/isodir/boot/minios.bin" ]; then
    echo "✓ Kernel found at build/isodir/boot/minios.bin"
    ls -lh build/isodir/boot/minios.bin
else
    echo "✗ Kernel NOT found at build/isodir/boot/minios.bin"
    echo "  This will cause boot failure!"
fi
echo ""

# Check GRUB files
echo "8. GRUB configuration:"
if [ -f "build/isodir/boot/grub/grub.cfg" ]; then
    echo "✓ GRUB config found"
    echo "Contents:"
    cat build/isodir/boot/grub/grub.cfg
else
    echo "✗ GRUB config NOT found"
fi
echo ""

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [ "$SIGNATURE" == "55aa" ] && [ -f "build/isodir/boot/minios.bin" ] && [ -f "build/isodir/boot/grub/grub.cfg" ]; then
    echo "✓ ISO appears to be properly bootable"
    echo ""
    echo "If QEMU still fails, try:"
    echo "  ./test_qemu.sh"
    echo ""
    echo "Or manually:"
    echo "  qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d"
else
    echo "✗ ISO has issues - rebuild it:"
    echo "  make clean"
    echo "  make iso"
fi
echo ""
