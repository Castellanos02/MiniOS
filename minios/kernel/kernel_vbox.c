// kernel_vbox.c - VirtualBox-compatible kernel (simplified, no interrupts)
#include <stdint.h>

// VGA text mode
#define VGA_MEMORY 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

// Colors
#define COLOR_BLACK 0x0
#define COLOR_BLUE 0x1
#define COLOR_GREEN 0x2
#define COLOR_CYAN 0x3
#define COLOR_RED 0x4
#define COLOR_MAGENTA 0x5
#define COLOR_YELLOW 0xE
#define COLOR_WHITE 0xF
#define COLOR_LIGHT_GREEN 0xA
#define COLOR_LIGHT_CYAN 0xB
#define COLOR_LIGHT_RED 0xC

static uint16_t* const vga = (uint16_t*)VGA_MEMORY;
static uint8_t current_color = 0x0F;

// Simple string functions
static size_t strlen(const char* str) {
    size_t len = 0;
    while (str[len]) len++;
    return len;
}

// VGA functions
static void set_color(uint8_t fg, uint8_t bg) {
    current_color = (bg << 4) | fg;
}

static void putchar_at(char c, int x, int y, uint8_t color) {
    if (x >= 0 && x < VGA_WIDTH && y >= 0 && y < VGA_HEIGHT) {
        vga[y * VGA_WIDTH + x] = ((uint16_t)color << 8) | c;
    }
}

static void clear_screen(void) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga[i] = ((uint16_t)current_color << 8) | ' ';
    }
}

static void draw_box(int x, int y, int w, int h, uint8_t color) {
    // Top border
    for (int i = 0; i < w; i++) {
        char c = (i == 0) ? 201 : (i == w-1) ? 187 : 205;
        putchar_at(c, x + i, y, color);
    }
    
    // Bottom border
    for (int i = 0; i < w; i++) {
        char c = (i == 0) ? 200 : (i == w-1) ? 188 : 205;
        putchar_at(c, x + i, y + h - 1, color);
    }
    
    // Sides and fill
    for (int j = 1; j < h - 1; j++) {
        putchar_at(186, x, y + j, color);
        putchar_at(186, x + w - 1, y + j, color);
        for (int i = 1; i < w - 1; i++) {
            putchar_at(' ', x + i, y + j, color);
        }
    }
}

static void draw_text(const char* text, int x, int y, uint8_t color) {
    int i = 0;
    while (text[i] && x + i < VGA_WIDTH) {
        putchar_at(text[i], x + i, y, color);
        i++;
    }
}

static void draw_centered_text(const char* text, int y, uint8_t color) {
    int len = strlen(text);
    int x = (VGA_WIDTH - len) / 2;
    draw_text(text, x, y, color);
}

// Activities
static const char* activities[] = {
    "Take a 15-minute walk outside",
    "Do 10 minutes of stretching",
    "Read a chapter from your book",
    "Call a friend or family member",
    "Practice mindfulness meditation",
    "Work on a creative project",
    "Review your weekly goals",
    "Organize your workspace"
};
#define NUM_ACTIVITIES 8

static int current_activity = 0;

// Port I/O
static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

// Keyboard polling (no interrupts!)
static int keyboard_has_data(void) {
    return (inb(0x64) & 0x01) != 0;
}

static uint8_t keyboard_read_scancode(void) {
    while (!keyboard_has_data());
    return inb(0x60);
}

// Simple scancode to char (US keyboard)
static char scancode_to_char(uint8_t scancode) {
    // Only handle keys we need: A, R, N
    switch (scancode) {
        case 0x1E: return 'a';  // A key
        case 0x13: return 'r';  // R key  
        case 0x31: return 'n';  // N key
        default: return 0;
    }
}

// Check for keypress (non-blocking)
static char check_key(void) {
    if (keyboard_has_data()) {
        uint8_t scancode = inb(0x60);
        
        // Ignore key releases (bit 7 set)
        if (scancode & 0x80) {
            return 0;
        }
        
        return scancode_to_char(scancode);
    }
    return 0;
}

static void next_activity(void) {
    current_activity = (current_activity + 1) % NUM_ACTIVITIES;
}

// Draw the GUI
static void draw_gui(void) {
    clear_screen();
    
    // Header
    set_color(COLOR_YELLOW, COLOR_BLUE);
    for (int i = 0; i < VGA_WIDTH; i++) {
        putchar_at(' ', i, 0, current_color);
        putchar_at(' ', i, 1, current_color);
        putchar_at(' ', i, 2, current_color);
    }
    draw_centered_text("MiniOS - Neural Activity Suggester", 1, current_color);
    
    // Main content area
    set_color(COLOR_WHITE, COLOR_CYAN);
    draw_box(2, 4, VGA_WIDTH - 4, 15, current_color);
    
    // Activity suggestion
    set_color(COLOR_YELLOW, COLOR_CYAN);
    draw_text("Suggested Activity:", 4, 6, current_color);
    
    set_color(COLOR_WHITE, COLOR_CYAN);
    draw_text(activities[current_activity], 4, 8, (COLOR_CYAN << 4) | COLOR_LIGHT_GREEN);
    
    // Instructions
    set_color(COLOR_LIGHT_CYAN, COLOR_CYAN);
    draw_text("Press keys to interact:", 4, 11, current_color);
    
    set_color(COLOR_WHITE, COLOR_CYAN);
    draw_text("[A] Accept   [R] Reject   [N] Next", 4, 13, current_color);
    
    // Info box
    set_color(COLOR_WHITE, COLOR_MAGENTA);
    draw_box(2, 20, 38, 4, current_color);
    draw_text("SNN Model: Active", 4, 21, current_color);
    draw_text("Keyboard: Polling", 4, 22, current_color);
    
    set_color(COLOR_WHITE, COLOR_BLACK);
    draw_box(42, 20, 36, 4, current_color);
    draw_text("VirtualBox Edition", 44, 21, current_color);
    draw_text("Press A, R, or N keys", 44, 22, current_color);
    
    // Status bar
    set_color(COLOR_LIGHT_GREEN, COLOR_BLACK);
    for (int i = 0; i < VGA_WIDTH; i++) {
        putchar_at(' ', i, VGA_HEIGHT - 1, current_color);
    }
    draw_text(" MiniOS v1.0 | VirtualBox | Press A/R/N to interact", 
              0, VGA_HEIGHT - 1, current_color);
}

// Main kernel entry
void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr;
    
    // Verify multiboot
    if (magic != 0x2BADB002) {
        return;
    }
    
    // NO INTERRUPT SETUP - use polling instead for VirtualBox compatibility
    
    // Initialize
    current_activity = 0;
    
    // Draw initial GUI
    draw_gui();
    
    // Main loop with keyboard polling
    volatile int counter = 0;
    
    while (1) {
        // Check for keyboard input (polling, not interrupts!)
        char key = check_key();
        
        if (key == 'a') {
            // Accept
            set_color(COLOR_BLACK, COLOR_LIGHT_GREEN);
            draw_box(25, 10, 30, 3, current_color);
            draw_text("Activity Accepted!", 27, 11, current_color);
            
            // Delay
            for (volatile int i = 0; i < 5000000; i++);
            
            next_activity();
            draw_gui();
        }
        else if (key == 'r') {
            // Reject
            set_color(COLOR_WHITE, COLOR_LIGHT_RED);
            draw_box(25, 10, 30, 3, current_color);
            draw_text("Activity Rejected", 27, 11, current_color);
            
            // Delay
            for (volatile int i = 0; i < 5000000; i++);
            
            next_activity();
            draw_gui();
        }
        else if (key == 'n') {
            // Next
            next_activity();
            draw_gui();
        }
        
        // Blink indicator to show system is alive
        counter++;
        if ((counter / 100000) % 2 == 0) {
            putchar_at('*', VGA_WIDTH - 1, VGA_HEIGHT - 1, 
                      (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
        } else {
            putchar_at(' ', VGA_WIDTH - 1, VGA_HEIGHT - 1, 
                      (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
        }
    }
}
