// gui.c - Simple GUI framework
#include <stdint.h>
#include <stddef.h>

extern void terminal_write(const char* str);
extern void terminal_write_num(uint64_t num);
extern char keyboard_getchar(void);
extern int keyboard_has_char(void);
extern uint64_t get_timer_ticks(void);
extern uint32_t get_cpu_usage(void);
extern size_t get_memory_used(void);
extern void update_cpu_idle(void);
extern void update_cpu_busy(void);

// VGA text mode buffer
#define VGA_MEMORY 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

// GUI state
typedef struct {
    int x, y, width, height;
    uint8_t color;
    const char* text;
} Widget;

typedef struct {
    const char* title;
    const char* message;
    int visible;
    uint64_t show_time;
} Notification;

static Notification notification = {0};
static char input_buffer[256] = {0};
static int input_pos = 0;

// Colors
#define COLOR_BLACK 0x00
#define COLOR_BLUE 0x01
#define COLOR_GREEN 0x02
#define COLOR_CYAN 0x03
#define COLOR_RED 0x04
#define COLOR_MAGENTA 0x05
#define COLOR_BROWN 0x06
#define COLOR_LIGHT_GRAY 0x07
#define COLOR_DARK_GRAY 0x08
#define COLOR_LIGHT_BLUE 0x09
#define COLOR_LIGHT_GREEN 0x0A
#define COLOR_LIGHT_CYAN 0x0B
#define COLOR_LIGHT_RED 0x0C
#define COLOR_LIGHT_MAGENTA 0x0D
#define COLOR_YELLOW 0x0E
#define COLOR_WHITE 0x0F

static void draw_box(int x, int y, int width, int height, uint8_t color) {
    uint16_t* vga = (uint16_t*)VGA_MEMORY;
    
    // Top and bottom borders
    for (int i = 0; i < width; i++) {
        vga[(y * VGA_WIDTH) + x + i] = (color << 8) | (i == 0 ? 201 : (i == width - 1 ? 187 : 205));
        vga[((y + height - 1) * VGA_WIDTH) + x + i] = (color << 8) | (i == 0 ? 200 : (i == width - 1 ? 188 : 205));
    }
    
    // Side borders
    for (int i = 1; i < height - 1; i++) {
        vga[((y + i) * VGA_WIDTH) + x] = (color << 8) | 186;
        vga[((y + i) * VGA_WIDTH) + x + width - 1] = (color << 8) | 186;
        
        // Fill interior
        for (int j = 1; j < width - 1; j++) {
            vga[((y + i) * VGA_WIDTH) + x + j] = (color << 8) | ' ';
        }
    }
}

static void draw_text(int x, int y, const char* text, uint8_t color) {
    uint16_t* vga = (uint16_t*)VGA_MEMORY;
    int pos = 0;
    
    while (text[pos] && x + pos < VGA_WIDTH) {
        vga[(y * VGA_WIDTH) + x + pos] = (color << 8) | text[pos];
        pos++;
    }
}

static void draw_header(void) {
    draw_box(0, 0, VGA_WIDTH, 3, COLOR_LIGHT_BLUE);
    draw_text(2, 1, "MiniOS - Neural Activity Suggester", COLOR_YELLOW);
}

static void draw_status_bar(uint32_t cpu_usage, size_t mem_used) {
    draw_box(0, VGA_HEIGHT - 3, VGA_WIDTH, 3, COLOR_DARK_GRAY);
    
    char status[80];
    int pos = 0;
    
    // CPU usage
    status[pos++] = 'C';
    status[pos++] = 'P';
    status[pos++] = 'U';
    status[pos++] = ':';
    status[pos++] = ' ';
    status[pos++] = '0' + (cpu_usage / 10);
    status[pos++] = '0' + (cpu_usage % 10);
    status[pos++] = '%';
    status[pos++] = ' ';
    status[pos++] = ' ';
    
    // Memory usage
    status[pos++] = 'M';
    status[pos++] = 'e';
    status[pos++] = 'm';
    status[pos++] = ':';
    status[pos++] = ' ';
    
    uint32_t mem_kb = mem_used / 1024;
    if (mem_kb >= 1000) {
        status[pos++] = '0' + ((mem_kb / 1000) % 10);
        status[pos++] = ',';
    }
    if (mem_kb >= 100) {
        status[pos++] = '0' + ((mem_kb / 100) % 10);
    }
    if (mem_kb >= 10) {
        status[pos++] = '0' + ((mem_kb / 10) % 10);
    }
    status[pos++] = '0' + (mem_kb % 10);
    status[pos++] = 'K';
    status[pos++] = 'B';
    status[pos++] = 0;
    
    draw_text(2, VGA_HEIGHT - 2, status, COLOR_LIGHT_GREEN);
}

static void draw_main_panel(const char* activity, uint64_t latency_ms) {
    draw_box(2, 4, VGA_WIDTH - 4, VGA_HEIGHT - 8, COLOR_CYAN);
    
    draw_text(4, 5, "Current Time: 2026-02-16 10:30 AM", COLOR_WHITE);
    draw_text(4, 6, "Day: Monday", COLOR_WHITE);
    
    draw_text(4, 8, "Suggested Activity:", COLOR_YELLOW);
    draw_text(4, 9, activity, COLOR_LIGHT_GREEN);
    
    char latency_str[50] = "Inference Latency: ";
    int pos = 19;
    uint64_t lat = latency_ms;
    char lat_buf[20];
    int lat_pos = 0;
    
    if (lat == 0) {
        lat_buf[lat_pos++] = '0';
    } else {
        while (lat > 0) {
            lat_buf[lat_pos++] = '0' + (lat % 10);
            lat /= 10;
        }
    }
    
    for (int i = lat_pos - 1; i >= 0; i--) {
        latency_str[pos++] = lat_buf[i];
    }
    latency_str[pos++] = 'm';
    latency_str[pos++] = 's';
    latency_str[pos++] = 0;
    
    draw_text(4, 11, latency_str, COLOR_LIGHT_GRAY);
    
    draw_text(4, 13, "[A] Accept  [R] Reject  [I] Ignore", COLOR_LIGHT_CYAN);
}

static void show_notification(const char* title, const char* message) {
    notification.title = title;
    notification.message = message;
    notification.visible = 1;
    notification.show_time = get_timer_ticks();
}

static void draw_notification(void) {
    if (!notification.visible) return;
    
    // Hide after 3 seconds
    if (get_timer_ticks() - notification.show_time > 300) {
        notification.visible = 0;
        return;
    }
    
    int width = 40;
    int height = 5;
    int x = (VGA_WIDTH - width) / 2;
    int y = (VGA_HEIGHT - height) / 2;
    
    draw_box(x, y, width, height, COLOR_YELLOW);
    draw_text(x + 2, y + 1, notification.title, COLOR_BLACK);
    draw_text(x + 2, y + 2, notification.message, COLOR_BLACK);
}

// Python interface
extern int python_run_inference(const char* calendar_context, char* output_buffer, size_t buffer_size, uint64_t* latency_ms);
extern void python_log_feedback(const char* activity, const char* feedback);

static char current_activity[128] = "Loading...";
static uint64_t inference_latency = 0;

void init_gui(void) {
    // Initial inference
    char calendar_context[256] = "Monday, 10:30 AM, February 2026";
    python_run_inference(calendar_context, current_activity, sizeof(current_activity), &inference_latency);
}

void gui_main_loop(void) {
    uint64_t last_update = get_timer_ticks();
    uint32_t cpu_usage = 0;
    size_t mem_used = 0;
    
    while (1) {
        update_cpu_busy();
        
        // Update display every 100ms
        uint64_t current_ticks = get_timer_ticks();
        if (current_ticks - last_update > 10) {
            cpu_usage = get_cpu_usage();
            mem_used = get_memory_used();
            
            draw_header();
            draw_main_panel(current_activity, inference_latency);
            draw_status_bar(cpu_usage, mem_used);
            draw_notification();
            
            last_update = current_ticks;
        }
        
        // Handle input
        if (keyboard_has_char()) {
            update_cpu_busy();
            char c = keyboard_getchar();
            
            if (c == 'a' || c == 'A') {
                python_log_feedback(current_activity, "accept");
                show_notification("Feedback", "Activity accepted!");
                
                // Get new suggestion
                char calendar_context[256] = "Monday, 10:30 AM, February 2026";
                python_run_inference(calendar_context, current_activity, sizeof(current_activity), &inference_latency);
            } else if (c == 'r' || c == 'R') {
                python_log_feedback(current_activity, "reject");
                show_notification("Feedback", "Activity rejected!");
                
                // Get new suggestion
                char calendar_context[256] = "Monday, 10:30 AM, February 2026";
                python_run_inference(calendar_context, current_activity, sizeof(current_activity), &inference_latency);
            } else if (c == 'i' || c == 'I') {
                python_log_feedback(current_activity, "ignore");
                show_notification("Feedback", "Activity ignored");
            }
        } else {
            update_cpu_idle();
            asm volatile("hlt");
        }
    }
}
