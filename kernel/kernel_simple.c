// kernel_simple.c - Simplified 32-bit kernel for GRUB multiboot
#include <stdint.h>
#include <stddef.h>

// VGA text mode
#define VGA_MEMORY 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

static uint16_t* const vga_buffer = (uint16_t*)VGA_MEMORY;
static size_t terminal_row = 0;
static size_t terminal_column = 0;
static uint8_t terminal_color = 0x0F; // White on black

void terminal_clear(void) {
    for (size_t y = 0; y < VGA_HEIGHT; y++) {
        for (size_t x = 0; x < VGA_WIDTH; x++) {
            const size_t index = y * VGA_WIDTH + x;
            vga_buffer[index] = ((uint16_t)terminal_color << 8) | ' ';
        }
    }
    terminal_row = 0;
    terminal_column = 0;
}

void terminal_putchar(char c) {
    if (c == '\n') {
        terminal_column = 0;
        terminal_row++;
        if (terminal_row >= VGA_HEIGHT) {
            terminal_row = 0;
        }
        return;
    }
    
    const size_t index = terminal_row * VGA_WIDTH + terminal_column;
    vga_buffer[index] = ((uint16_t)terminal_color << 8) | c;
    
    terminal_column++;
    if (terminal_column >= VGA_WIDTH) {
        terminal_column = 0;
        terminal_row++;
        if (terminal_row >= VGA_HEIGHT) {
            terminal_row = 0;
        }
    }
}

void terminal_write(const char* str) {
    for (size_t i = 0; str[i] != '\0'; i++) {
        terminal_putchar(str[i]);
    }
}

void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr; // Unused
    
    terminal_clear();
    
    // Check if booted by multiboot-compliant bootloader
    if (magic != 0x2BADB002) {
        terminal_write("ERROR: Not booted by multiboot loader!\n");
        return;
    }
    
    terminal_color = 0x0B; // Cyan
    terminal_write("========================================\n");
    terminal_color = 0x0E; // Yellow
    terminal_write("       MiniOS v1.0 - GRUB Edition\n");
    terminal_color = 0x0B;
    terminal_write("========================================\n\n");
    
    terminal_color = 0x0A; // Green
    terminal_write("Boot Status:\n");
    terminal_color = 0x0F;
    terminal_write("  [OK] Multiboot header verified\n");
    terminal_write("  [OK] Kernel loaded successfully\n");
    terminal_write("  [OK] VGA text mode initialized\n");
    terminal_write("  [OK] Protected mode active\n\n");
    
    terminal_color = 0x0E;
    terminal_write("System Information:\n");
    terminal_color = 0x07;
    terminal_write("  Architecture: x86 (32-bit)\n");
    terminal_write("  Bootloader: GRUB\n");
    terminal_write("  Display: VGA Text Mode (80x25)\n\n");
    
    terminal_color = 0x0D; // Magenta
    terminal_write("MiniOS Features:\n");
    terminal_color = 0x07;
    terminal_write("  * Neural Activity Suggester\n");
    terminal_write("  * Spiking Neural Network\n");
    terminal_write("  * Performance Monitoring\n");
    terminal_write("  * Feedback Learning System\n\n");
    
    terminal_color = 0x0C; // Red
    terminal_write("Note: Full GUI requires simulators\n");
    terminal_color = 0x07;
    terminal_write("Run './minios_gui' for complete experience\n\n");
    
    terminal_color = 0x0A;
    terminal_write("Kernel initialization complete!\n");
    terminal_write("System is running...\n");
    
    // Halt
    while (1) {
        __asm__ volatile("hlt");
    }
}
