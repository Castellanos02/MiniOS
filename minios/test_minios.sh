#!/bin/bash
# test_minios.sh - Test script for MiniOS simulator

echo "========================================="
echo "MiniOS Simulator Test Script"
echo "========================================="
echo ""

# Check if simulator exists
if [ ! -f "./minios_simulator" ]; then
    echo "❌ Error: minios_simulator not found"
    echo "   Run: gcc -o minios_simulator minios_simulator.c -lm"
    exit 1
fi

# Check if executable
if [ ! -x "./minios_simulator" ]; then
    echo "⚠️  Making simulator executable..."
    chmod +x ./minios_simulator
fi

echo "✓ Simulator found and executable"
echo ""
echo "Terminal capabilities:"
echo "  - TERM: $TERM"
echo "  - Colors: $(tput colors 2>/dev/null || echo 'unknown')"
echo ""

# Check dependencies
echo "Checking system..."
if command -v gcc &> /dev/null; then
    echo "✓ GCC installed: $(gcc --version | head -n1)"
else
    echo "⚠️  GCC not found (needed for recompiling)"
fi
echo ""

echo "========================================="
echo "Starting MiniOS Simulator..."
echo "========================================="
echo ""
echo "Controls:"
echo "  A - Accept activity"
echo "  R - Reject activity"
echo "  I - Ignore activity"
echo "  L - View logs"
echo "  Q - Quit"
echo ""
echo "Press any key to start..."
read -n 1 -s

# Clear screen and run
clear
./minios_simulator

# Exit status
EXIT_CODE=$?
echo ""
echo "========================================="
echo "Simulator exited with code: $EXIT_CODE"
echo "========================================="

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Troubleshooting tips:"
    echo "  1. Try: reset (to reset terminal)"
    echo "  2. Check terminal supports ANSI colors"
    echo "  3. Recompile: gcc -o minios_simulator minios_simulator.c -lm"
fi
