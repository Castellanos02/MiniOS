// kernel_main.c - Main kernel entry point
// Now compatible with GRUB multiboot (32-bit entry)
#include <stdint.h>
#include <stddef.h>

// Multiboot info structures
struct multiboot_info {
    uint32_t flags;
    uint32_t mem_lower;
    uint32_t mem_upper;
    uint32_t boot_device;
    uint32_t cmdline;
    uint32_t mods_count;
    uint32_t mods_addr;
} __attribute__((packed));

// VGA text mode buffer
#define VGA_MEMORY 0xC00B8000  // Identity mapped
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

// Framebuffer for GUI (assuming 1024x768x32)
#define FB_ADDRESS 0xFD000000
#define FB_WIDTH 1024
#define FB_HEIGHT 768

// Memory management
#define HEAP_START 0x100000
#define HEAP_SIZE 0x1000000

// Port I/O
static inline void outb(uint16_t port, uint8_t value) {
    asm volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    asm volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

// Terminal functions
static uint32_t terminal_row = 0;
static uint32_t terminal_column = 0;
static uint8_t terminal_color = 0x0F;

void terminal_clear(void) {
    uint16_t* vga = (uint16_t*)VGA_MEMORY;
    for (size_t i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga[i] = (terminal_color << 8) | ' ';
    }
    terminal_row = 0;
    terminal_column = 0;
}

void terminal_putchar(char c) {
    if (c == '\n') {
        terminal_column = 0;
        terminal_row++;
        if (terminal_row >= VGA_HEIGHT) {
            terminal_row = VGA_HEIGHT - 1;
            // Scroll
            uint16_t* vga = (uint16_t*)VGA_MEMORY;
            for (size_t i = 0; i < VGA_WIDTH * (VGA_HEIGHT - 1); i++) {
                vga[i] = vga[i + VGA_WIDTH];
            }
            for (size_t i = 0; i < VGA_WIDTH; i++) {
                vga[VGA_WIDTH * (VGA_HEIGHT - 1) + i] = (terminal_color << 8) | ' ';
            }
        }
        return;
    }
    
    uint16_t* vga = (uint16_t*)VGA_MEMORY;
    vga[terminal_row * VGA_WIDTH + terminal_column] = (terminal_color << 8) | c;
    
    terminal_column++;
    if (terminal_column >= VGA_WIDTH) {
        terminal_column = 0;
        terminal_row++;
        if (terminal_row >= VGA_HEIGHT) {
            terminal_row = VGA_HEIGHT - 1;
        }
    }
}

void terminal_write(const char* str) {
    while (*str) {
        terminal_putchar(*str++);
    }
}

void terminal_write_num(uint64_t num) {
    char buffer[20];
    int i = 0;
    if (num == 0) {
        terminal_putchar('0');
        return;
    }
    while (num > 0) {
        buffer[i++] = '0' + (num % 10);
        num /= 10;
    }
    while (i > 0) {
        terminal_putchar(buffer[--i]);
    }
}

// Simple memory allocator
static uint8_t* heap_ptr = (uint8_t*)HEAP_START;

void* kmalloc(size_t size) {
    void* ptr = heap_ptr;
    heap_ptr += size;
    if ((uintptr_t)heap_ptr >= HEAP_START + HEAP_SIZE) {
        return NULL;
    }
    return ptr;
}

// Timer
static volatile uint64_t timer_ticks = 0;

void timer_handler(void) {
    timer_ticks++;
}

void init_timer(uint32_t frequency) {
    uint32_t divisor = 1193180 / frequency;
    outb(0x43, 0x36);
    outb(0x40, divisor & 0xFF);
    outb(0x40, (divisor >> 8) & 0xFF);
}

uint64_t get_timer_ticks(void) {
    return timer_ticks;
}

// IDT structures
struct idt_entry {
    uint16_t base_low;
    uint16_t selector;
    uint8_t ist;
    uint8_t flags;
    uint16_t base_mid;
    uint32_t base_high;
    uint32_t reserved;
} __attribute__((packed));

struct idt_ptr {
    uint16_t limit;
    uint64_t base;
} __attribute__((packed));

static struct idt_entry idt[256];
static struct idt_ptr idtp;

void idt_set_gate(uint8_t num, uint64_t handler) {
    idt[num].base_low = handler & 0xFFFF;
    idt[num].base_mid = (handler >> 16) & 0xFFFF;
    idt[num].base_high = (handler >> 32) & 0xFFFFFFFF;
    idt[num].selector = 0x08;
    idt[num].ist = 0;
    idt[num].flags = 0x8E;
    idt[num].reserved = 0;
}

extern void isr_timer(void);
extern void isr_keyboard(void);

void init_idt(void) {
    idtp.limit = sizeof(idt) - 1;
    idtp.base = (uint64_t)&idt;
    
    // Set up timer and keyboard
    idt_set_gate(32, (uint64_t)isr_timer);
    idt_set_gate(33, (uint64_t)isr_keyboard);
    
    // Load IDT
    asm volatile("lidt %0" : : "m"(idtp));
    
    // Enable interrupts
    asm volatile("sti");
}

void init_pic(void) {
    // Remap PIC
    outb(0x20, 0x11);
    outb(0xA0, 0x11);
    outb(0x21, 0x20);
    outb(0xA1, 0x28);
    outb(0x21, 0x04);
    outb(0xA1, 0x02);
    outb(0x21, 0x01);
    outb(0xA1, 0x01);
    outb(0x21, 0x0);
    outb(0xA1, 0x0);
}

// Keyboard handling
#define KEYBOARD_BUFFER_SIZE 128
static char keyboard_buffer[KEYBOARD_BUFFER_SIZE];
static volatile int keyboard_head = 0;
static volatile int keyboard_tail = 0;

void keyboard_handler(void) {
    uint8_t scancode = inb(0x60);
    
    // Simple scancode to ASCII conversion (US layout)
    static const char scancode_to_ascii[] = {
        0, 0, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b',
        '\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n',
        0, 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`', 0, '\\',
        'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, 0, 0, ' '
    };
    
    if (scancode < sizeof(scancode_to_ascii) && scancode_to_ascii[scancode]) {
        int next = (keyboard_head + 1) % KEYBOARD_BUFFER_SIZE;
        if (next != keyboard_tail) {
            keyboard_buffer[keyboard_head] = scancode_to_ascii[scancode];
            keyboard_head = next;
        }
    }
}

char keyboard_getchar(void) {
    while (keyboard_head == keyboard_tail) {
        asm volatile("hlt");
    }
    char c = keyboard_buffer[keyboard_tail];
    keyboard_tail = (keyboard_tail + 1) % KEYBOARD_BUFFER_SIZE;
    return c;
}

int keyboard_has_char(void) {
    return keyboard_head != keyboard_tail;
}

// CPU usage tracking
static uint64_t idle_count = 0;
static uint64_t total_count = 0;

void update_cpu_idle(void) {
    idle_count++;
    total_count++;
}

void update_cpu_busy(void) {
    total_count++;
}

uint32_t get_cpu_usage(void) {
    if (total_count == 0) return 0;
    uint32_t usage = ((total_count - idle_count) * 100) / total_count;
    idle_count = 0;
    total_count = 0;
    return usage;
}

// Memory usage tracking
size_t get_memory_used(void) {
    return (size_t)(heap_ptr - (uint8_t*)HEAP_START);
}

// Forward declarations for GUI and Python
void init_gui(void);
void gui_main_loop(void);
int python_init(void);
int python_run_snn_model(void);

// Kernel entry point
void kernel_main(void) {
    terminal_clear();
    terminal_write("MiniOS v1.0\n");
    terminal_write("Initializing...\n");
    
    // Initialize interrupts
    init_pic();
    init_idt();
    init_timer(100); // 100Hz
    
    terminal_write("Timer initialized\n");
    terminal_write("Keyboard initialized\n");
    
    // Initialize Python runtime
    terminal_write("Initializing Python runtime...\n");
    if (python_init() != 0) {
        terminal_write("Python initialization failed\n");
    } else {
        terminal_write("Python initialized\n");
    }
    
    // Initialize GUI
    terminal_write("Initializing GUI...\n");
    init_gui();
    
    terminal_write("Starting main loop...\n");
    
    // Main loop
    gui_main_loop();
    
    // Should never reach here
    while (1) {
        asm volatile("hlt");
    }
}
