// kernel_carplay.c - CarPlay-style interface with FPPS scheduler
// Works in QEMU and VirtualBox with proactive ML, memory tracking,
// and a Fixed-Priority Preemptive Scheduler (FPPS) driven by PIT IRQ0.

#include <stdint.h>
#include <stddef.h>

// Use Case Neuromorphic SNN (replaces old ML system)
#include "usecase_snn_weights.h"

// =============================================================================
// FIXED-PRIORITY PREEMPTIVE SCHEDULER (FPPS)
// Priority 0 = UI/Input (highest)
// Priority 1 = SNN Inference Engine
// Priority 2 = System Metrics / Proactive AI
// Priority 3 = Idle task (executes hlt)
//
// All scheduler types, constants, functions, and globals are declared in
// kernel/scheduler.h and are part of the public, externally-callable API.
// See scheduler-API.md for the full reference.
// =============================================================================

#include "scheduler.h"

Task               g_tasks[NUM_TASKS];
uint8_t            g_ready_mask   = 0;
uint8_t            g_current_task = 0;
volatile uint32_t  g_tick         = 0;
uint8_t            g_task_stacks[NUM_TASKS][TASK_STACK_SZ] __attribute__((aligned(16)));

// =============================================================================
// SIMPLIFIED ML & MEMORY TRACKING (from kernel_enhanced.c)
// =============================================================================

typedef struct {
    uint32_t cycles;
    uint8_t time_segment;
    uint8_t energy_level;
    uint8_t engagement;
    uint32_t idle_cycles;
    uint32_t total_accepts;
    uint32_t total_rejects;
    uint8_t activity_prefs[20];
    uint8_t current_hour;    // 0-23
    uint8_t current_minute;  // 0-59
    uint8_t day_of_week;     // 0=Mon, 6=Sun
} MLContext;

static MLContext g_ml = {0};

typedef struct {
    uint32_t vga_updates;
    uint32_t context_updates;
    uint32_t variable_changes;
} MemStats;

static MemStats g_mem = {0};

typedef struct {
    const char* desc;
    uint8_t category;
    uint8_t energy_req;
    uint8_t time_pref;
} Activity;

static Activity g_activities[] = {
    {"Take a 15-minute walk outside", 0, 60, 0},
    {"Do 10 minutes of stretching", 0, 40, 0},
    {"Quick 5-minute workout", 0, 80, 0},
    {"Review your weekly goals", 1, 50, 0},
    {"Plan tomorrow's tasks", 1, 40, 1},
    {"Practice a new skill", 1, 60, 1},
    {"Call a friend or family", 2, 50, 2},
    {"Send a thoughtful message", 2, 30, 3},
    {"Schedule coffee with colleague", 2, 40, 1},
    {"Organize your workspace", 3, 50, 0},
    {"Clear your email inbox", 3, 45, 1},
    {"Update your to-do list", 3, 35, 3},
    {"Work on creative project", 4, 70, 3},
    {"Journal for 10 minutes", 4, 30, 2},
    {"Brainstorm new ideas", 4, 60, 1},
    {"Practice mindfulness meditation", 5, 20, 2},
    {"Take a few deep breaths", 5, 10, 3},
    {"Read a chapter from book", 5, 25, 2},
    {"Watch educational video", 6, 35, 1},
    {"Read article about something new", 6, 40, 1}
};
#define NUM_ACTIVITIES 20

// =============================================================================
// CALENDAR EVENTS
// =============================================================================

#define MAX_EVENTS 20

typedef struct {
    uint8_t hour;       // 0-23
    uint8_t minute;     // 0-59
    uint8_t duration;   // minutes
    const char* title;
    uint8_t is_suggestion; // 0=scheduled, 1=AI suggestion
    uint8_t category;   // Activity category
} CalendarEvent;

static CalendarEvent g_events[MAX_EVENTS] = {0};
static uint8_t g_event_count = 0;

// Add scheduled events (pre-populated)
static void init_calendar(void) {
    g_event_count = 0;
    
    // Add some sample scheduled events
    g_events[g_event_count++] = (CalendarEvent){9, 0, 60, "Team Meeting", 0, 1};
    g_events[g_event_count++] = (CalendarEvent){11, 30, 30, "Lunch Break", 0, 5};
    g_events[g_event_count++] = (CalendarEvent){14, 0, 45, "Project Work", 0, 3};
    g_events[g_event_count++] = (CalendarEvent){16, 30, 15, "Coffee Break", 0, 5};
}

// Add AI suggestion to calendar
static void add_suggestion_to_calendar(uint8_t activity_idx, uint8_t hour, uint8_t minute) {
    if (g_event_count >= MAX_EVENTS) return;
    
    g_events[g_event_count++] = (CalendarEvent){
        hour,
        minute,
        15,  // Default 15 min duration
        g_activities[activity_idx].desc,
        1,   // Is suggestion
        g_activities[activity_idx].category
    };
}

// =============================================================================
// VGA GRAPHICS
// =============================================================================

#define VGA_MEMORY 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

// Extended color palette for CarPlay style
#define COLOR_BLACK 0x0
#define COLOR_BLUE 0x1
#define COLOR_GREEN 0x2
#define COLOR_CYAN 0x3
#define COLOR_RED 0x4
#define COLOR_MAGENTA 0x5
#define COLOR_BROWN 0x6
#define COLOR_LIGHT_GRAY 0x7
#define COLOR_DARK_GRAY 0x8
#define COLOR_LIGHT_BLUE 0x9
#define COLOR_LIGHT_GREEN 0xA
#define COLOR_LIGHT_CYAN 0xB
#define COLOR_LIGHT_RED 0xC
#define COLOR_LIGHT_MAGENTA 0xD
#define COLOR_YELLOW 0xE
#define COLOR_WHITE 0xF

static uint16_t* const vga = (uint16_t*)VGA_MEMORY;
static uint8_t current_color = 0x0F;

static size_t strlen(const char* str) {
    size_t len = 0;
    while (str[len]) len++;
    return len;
}

static void mem_track_vga(void) { g_mem.vga_updates++; }
static void mem_track_ctx(void) { g_mem.context_updates++; }
static void mem_track_var(void) { g_mem.variable_changes++; }

static void set_color(uint8_t fg, uint8_t bg) {
    current_color = (bg << 4) | fg;
}

static void putchar_at(char c, int x, int y, uint8_t color) {
    if (x >= 0 && x < VGA_WIDTH && y >= 0 && y < VGA_HEIGHT) {
        vga[y * VGA_WIDTH + x] = ((uint16_t)color << 8) | c;
        mem_track_vga();
    }
}

static void clear_screen(void) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga[i] = ((uint16_t)current_color << 8) | ' ';
    }
    mem_track_vga();
}

static void draw_box(int x, int y, int w, int h, uint8_t color) {
    for (int i = 0; i < w; i++) {
        char c = (i == 0) ? 218 : (i == w-1) ? 191 : 196;
        putchar_at(c, x + i, y, color);
    }
    for (int i = 0; i < w; i++) {
        char c = (i == 0) ? 192 : (i == w-1) ? 217 : 196;
        putchar_at(c, x + i, y + h - 1, color);
    }
    for (int j = 1; j < h - 1; j++) {
        putchar_at(179, x, y + j, color);
        putchar_at(179, x + w - 1, y + j, color);
        for (int i = 1; i < w - 1; i++) {
            putchar_at(' ', x + i, y + j, color);
        }
    }
}

static void fill_box(int x, int y, int w, int h, uint8_t color) {
    for (int j = 0; j < h; j++) {
        for (int i = 0; i < w; i++) {
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

static void uint_to_str(uint32_t num, char* buf) {
    if (num == 0) {
        buf[0] = '0';
        buf[1] = '\0';
        return;
    }
    int i = 0;
    while (num > 0) {
        buf[i++] = '0' + (num % 10);
        num /= 10;
    }
    buf[i] = '\0';
    for (int j = 0; j < i/2; j++) {
        char t = buf[j];
        buf[j] = buf[i-1-j];
        buf[i-1-j] = t;
    }
}

static void two_digit_str(uint8_t num, char* buf) {
    buf[0] = '0' + (num / 10);
    buf[1] = '0' + (num % 10);
    buf[2] = '\0';
}

// =============================================================================
// KEYBOARD INPUT
// =============================================================================

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

static inline void outb(uint16_t port, uint8_t val) {
    __asm__ volatile("outb %0, %1" :: "a"(val), "Nd"(port));
}

static inline void io_wait(void) {
    outb(0x80, 0x00);  // write to POST port — safe throwaway, adds ~1 µs delay
}

static int keyboard_has_data(void) {
    return (inb(0x64) & 0x01) != 0;
}

static char scancode_to_char(uint8_t sc) {
    static const char map[] = {
        0, 0, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b',
        '\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n',
        0, 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`', 0, '\\',
        'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, '*', 0, ' '
    };
    if (sc < sizeof(map)) return map[sc];
    return 0;
}

static char check_key(void) {
    if (keyboard_has_data()) {
        uint8_t sc = inb(0x60);
        if (!(sc & 0x80)) {
            return scancode_to_char(sc);
        }
    }
    return 0;
}

// =============================================================================
// IDT / PIC / PIT INITIALISATION
// (See scheduler-readME.md "Hardware Initialisation" for the full rationale.)
// =============================================================================

// 32-bit interrupt gate descriptor (8 bytes)
typedef struct __attribute__((packed)) {
    uint16_t offset_low;   // bits  0-15 of handler address
    uint16_t selector;     // code segment selector (0x08 = GRUB's ring-0 code seg)
    uint8_t  zero;         // always 0
    uint8_t  type_attr;    // 0x8E: P=1, DPL=0, type=1110 (32-bit interrupt gate)
    uint16_t offset_high;  // bits 16-31 of handler address
} IDTEntry;

typedef struct __attribute__((packed)) {
    uint16_t limit;   // sizeof(idt_table) - 1
    uint32_t base;    // linear address of idt_table
} IDTPointer;

static IDTEntry   g_idt[256];
static IDTPointer g_idtp;

void idt_set_gate(uint8_t vec, uint32_t handler) {
    g_idt[vec].offset_low  = (uint16_t)(handler & 0xFFFF);
    g_idt[vec].selector    = 0x08;
    g_idt[vec].zero        = 0;
    g_idt[vec].type_attr   = 0x8E;
    g_idt[vec].offset_high = (uint16_t)((handler >> 16) & 0xFFFF);
}

void idt_install(void) {
    for (int i = 0; i < 256; i++) {
        g_idt[i].offset_low  = 0;
        g_idt[i].selector    = 0x08;
        g_idt[i].zero        = 0;
        g_idt[i].type_attr   = 0x0E;
        g_idt[i].offset_high = 0;
    }
    idt_set_gate(PIT_VECTOR, (uint32_t)isr_pit);

    g_idtp.limit = (uint16_t)(sizeof(g_idt) - 1);
    g_idtp.base  = (uint32_t)g_idt;
    __asm__ volatile("lidt %0" :: "m"(g_idtp));
}

void pic_remap(void) {
    outb(0x20, 0x11); io_wait();   // ICW1: init master
    outb(0xA0, 0x11); io_wait();   // ICW1: init slave
    outb(0x21, 0x20); io_wait();   // ICW2: master base vector = 0x20
    outb(0xA1, 0x28); io_wait();   // ICW2: slave base vector  = 0x28
    outb(0x21, 0x04); io_wait();   // ICW3: master has slave on IR2
    outb(0xA1, 0x02); io_wait();   // ICW3: slave cascade identity = 2
    outb(0x21, 0x01); io_wait();   // ICW4: 8086 mode
    outb(0xA1, 0x01); io_wait();
    outb(0x21, 0xFE);              // OCW1: unmask IRQ0 only
    outb(0xA1, 0xFF);              // OCW1: mask all slave IRQs
}

void pit_init(void) {
    outb(0x43, 0x36);
    outb(0x40, (uint8_t)(PIT_DIVISOR & 0xFF));
    outb(0x40, (uint8_t)((PIT_DIVISOR >> 8) & 0xFF));
}

// =============================================================================
// ML FUNCTIONS (simplified from kernel_enhanced.c)
// =============================================================================

static void ml_update_context(uint32_t cycles, uint8_t idle) {
    g_ml.cycles += cycles;
    
    uint32_t minutes = (g_ml.cycles / 1000000) % (24 * 60);
    g_ml.current_hour = (minutes / 60) % 24;
    g_ml.current_minute = minutes % 60;
    
    // Calculate day of week (simple: 0=Mon, cycles from Monday 00:00)
    uint32_t total_minutes = g_ml.cycles / 1000000;
    uint32_t days = total_minutes / (24 * 60);
    g_ml.day_of_week = days % 7;  // 0=Mon, 6=Sun
    
    if (g_ml.current_hour >= 6 && g_ml.current_hour < 12) g_ml.time_segment = 0;
    else if (g_ml.current_hour >= 12 && g_ml.current_hour < 17) g_ml.time_segment = 1;
    else if (g_ml.current_hour >= 17 && g_ml.current_hour < 22) g_ml.time_segment = 2;
    else g_ml.time_segment = 3;
    
    // Better energy model: gradual increase in morning, peak midday, decline evening
    if (g_ml.current_hour >= 6 && g_ml.current_hour < 9) {
        // Morning: 60-80 (waking up, energy building)
        g_ml.energy_level = 60 + ((g_ml.current_hour - 6) * 7);
    } else if (g_ml.current_hour >= 9 && g_ml.current_hour < 12) {
        // Late morning: 80-90 (peak morning energy)
        g_ml.energy_level = 80 + ((g_ml.current_hour - 9) * 3);
    } else if (g_ml.current_hour >= 12 && g_ml.current_hour < 14) {
        // Lunch: 70-80 (slight dip)
        g_ml.energy_level = 75;
    } else if (g_ml.current_hour >= 14 && g_ml.current_hour < 17) {
        // Afternoon: 65-75
        g_ml.energy_level = 70;
    } else if (g_ml.current_hour >= 17 && g_ml.current_hour < 22) {
        // Evening: 50-65 (declining)
        g_ml.energy_level = 65 - ((g_ml.current_hour - 17) * 3);
    } else {
        // Night/early morning: 30-50 (low)
        g_ml.energy_level = 35;
    }
    
    uint32_t total = g_ml.total_accepts + g_ml.total_rejects;
    g_ml.engagement = total > 0 ? (g_ml.total_accepts * 100) / total : 50;
    
    if (idle) g_ml.idle_cycles += cycles;
    mem_track_ctx();
}

static uint8_t ml_score_activity(uint8_t idx) {
    if (idx >= NUM_ACTIVITIES) return 0;
    Activity* act = &g_activities[idx];
    uint8_t score = 0;
    
    if (act->time_pref == 3) score += 20;
    else if (act->time_pref == g_ml.time_segment) score += 30;
    else score += 5;
    
    int diff = act->energy_req - g_ml.energy_level;
    if (diff < 0) diff = -diff;
    if (diff < 15) score += 30;
    else if (diff < 30) score += 20;
    else score += 5;
    
    if (idx < 20) score += (g_ml.activity_prefs[idx] * 2);
    if (g_ml.engagement > 50) score += 10;
    
    return score;
}

static uint8_t ml_suggest_activity(void) {
    uint8_t best = 0, best_score = 0;
    for (uint8_t i = 0; i < NUM_ACTIVITIES; i++) {
        uint8_t score = ml_score_activity(i);
        if (score > best_score) {
            best_score = score;
            best = i;
        }
    }
    return best;
}

// =============================================================================
// NEUROMORPHIC SNN PROACTIVE SUGGESTIONS
// =============================================================================

// Get idle time until next calendar event
static int get_idle_minutes_until_next_event(void) {
    int current_mins = g_ml.current_hour * 60 + g_ml.current_minute;
    int next_event_mins = 24 * 60;  // End of day default
    
    // Find next event
    for (uint8_t i = 0; i < g_event_count; i++) {
        int event_mins = g_events[i].hour * 60 + g_events[i].minute;
        if (event_mins > current_mins && event_mins < next_event_mins) {
            next_event_mins = event_mins;
        }
    }
    
    int idle_mins = next_event_mins - current_mins;
    
    // If no events found (idle_mins >= full day), use time-of-day heuristic
    if (idle_mins >= 24 * 60 || idle_mins <= 0) {
        // Estimate based on time of day
        if (g_ml.current_hour >= 6 && g_ml.current_hour < 9) {
            return 60;  // Morning: 1 hour blocks
        } else if (g_ml.current_hour >= 9 && g_ml.current_hour < 12) {
            return 120; // Mid-morning: 2 hour blocks
        } else if (g_ml.current_hour >= 12 && g_ml.current_hour < 14) {
            return 60;  // Lunch: 1 hour
        } else if (g_ml.current_hour >= 14 && g_ml.current_hour < 17) {
            return 90;  // Afternoon: 1.5 hours
        } else if (g_ml.current_hour >= 17 && g_ml.current_hour < 20) {
            return 120; // Evening: 2 hours
        } else if (g_ml.current_hour >= 20 && g_ml.current_hour < 22) {
            return 90;  // Night: 1.5 hours
        } else {
            return 30;  // Late night: 30 min
        }
    }
    
    return idle_mins;
}

// Get neuromorphic SNN suggestion
static const char* get_snn_suggestion_wrapper(int* out_activity_idx) {
    static const char* last_suggestion = NULL;  // Track last suggestion
    static uint8_t retry_count = 0;
    
    // Calculate idle time
    int idle_mins = get_idle_minutes_until_next_event();
    
    // Check if there's an upcoming meeting
    int has_meeting = 0;
    int current_mins = g_ml.current_hour * 60 + g_ml.current_minute;
    for (uint8_t i = 0; i < g_event_count; i++) {
        int event_mins = g_events[i].hour * 60 + g_events[i].minute;
        if (event_mins > current_mins && event_mins < current_mins + 60) {
            has_meeting = 1;
            break;
        }
    }
    
    // Vary the engagement and energy slightly to get different suggestions
    int varied_energy = g_ml.energy_level;
    int varied_engagement = g_ml.engagement;
    
    // Add some variation based on retry count to avoid repetition
    if (retry_count > 0) {
        varied_energy = (g_ml.energy_level + retry_count * 15) % 100;
        varied_engagement = (g_ml.engagement + retry_count * 20) % 100;
    }
    
    // Get SNN suggestion (using renamed function to avoid conflict)
    const char* suggestion = get_snn_proactive_suggestion(
        g_ml.current_hour,
        g_ml.current_minute,
        g_ml.day_of_week,
        varied_energy,
        varied_engagement,
        idle_mins,
        has_meeting,
        (g_ml.total_accepts > 10) ? 10 : g_ml.total_accepts,
        (g_ml.total_rejects > 10) ? 10 : g_ml.total_rejects
    );
    
    // If same as last suggestion, try again with variation
    if (last_suggestion != NULL && retry_count < 5) {
        // Simple string comparison (works because we're comparing pointers to string literals)
        uint8_t same = 1;
        const char* p1 = last_suggestion;
        const char* p2 = suggestion;
        while (*p1 && *p2) {
            if (*p1 != *p2) {
                same = 0;
                break;
            }
            p1++;
            p2++;
        }
        if (*p1 != *p2) same = 0;
        
        if (same) {
            retry_count++;
            return get_snn_suggestion_wrapper(out_activity_idx);  // Recursively try again
        }
    }
    
    // Reset retry count and save this suggestion
    retry_count = 0;
    last_suggestion = suggestion;
    
    // Find matching activity index (for calendar integration)
    *out_activity_idx = 0;  // Default
    for (int i = 0; i < UC_OUTPUT_SIZE; i++) {
        if (suggestion == ACTIVITY_NAMES[i]) {
            *out_activity_idx = i % NUM_ACTIVITIES;  // Map to existing activities
            break;
        }
    }
    
    return suggestion;
}

static void ml_record_feedback(uint8_t idx, uint8_t accepted) {
    if (accepted) {
        g_ml.total_accepts++;
        if (idx < 20 && g_ml.activity_prefs[idx] < 10) g_ml.activity_prefs[idx]++;
    } else {
        g_ml.total_rejects++;
        if (idx < 20 && g_ml.activity_prefs[idx] > 0) g_ml.activity_prefs[idx]--;
    }
    g_ml.idle_cycles = 0;
    mem_track_var();
}

// =============================================================================
// CARPLAY-STYLE HOME SCREEN
// =============================================================================

static void draw_app_icon(int x, int y, const char* icon, const char* name, 
                         uint8_t fg_color, uint8_t bg_color, uint8_t selected) {
    // Draw app tile
    uint8_t border_color = selected ? 
        ((COLOR_YELLOW << 4) | fg_color) : 
        ((bg_color << 4) | fg_color);
    
    fill_box(x, y, 16, 6, (bg_color << 4) | fg_color);
    draw_box(x, y, 16, 6, border_color);
    
    // Draw icon (centered)
    int icon_len = strlen(icon);
    int icon_x = x + (16 - icon_len) / 2;
    draw_text(icon, icon_x, y + 2, (bg_color << 4) | COLOR_WHITE);
    
    // Draw name (centered)
    int name_len = strlen(name);
    int name_x = x + (16 - name_len) / 2;
    draw_text(name, name_x, y + 4, (bg_color << 4) | COLOR_WHITE);
}

static void draw_home_screen(uint8_t selected_app) {
    clear_screen();
    
    // Dark background
    set_color(COLOR_WHITE, COLOR_BLACK);
    for (int y = 0; y < VGA_HEIGHT; y++) {
        for (int x = 0; x < VGA_WIDTH; x++) {
            putchar_at(' ', x, y, current_color);
        }
    }
    
    // Title bar
    fill_box(0, 0, VGA_WIDTH, 3, (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    
    // Time display
    char time_str[10];
    char hour_buf[3], min_buf[3];
    two_digit_str(g_ml.current_hour, hour_buf);
    two_digit_str(g_ml.current_minute, min_buf);
    time_str[0] = hour_buf[0];
    time_str[1] = hour_buf[1];
    time_str[2] = ':';
    time_str[3] = min_buf[0];
    time_str[4] = min_buf[1];
    time_str[5] = '\0';
    draw_text(time_str, VGA_WIDTH - 8, 1, (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    
    // App name
    draw_centered_text("MiniOS CarPlay", 1, (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    
    // Apps grid (2x2 for now)
    int start_x = 20;
    int start_y = 6;
    int spacing = 20;
    
    // Calendar app (position 0)
    draw_app_icon(start_x, start_y, 
                  " [CAL] ", "Calendar", 
                  COLOR_WHITE, COLOR_RED, 
                  selected_app == 0);
    
    // Maps app (position 1)
    draw_app_icon(start_x + spacing, start_y,
                  " [MAP] ", "Maps",
                  COLOR_WHITE, COLOR_LIGHT_BLUE,
                  selected_app == 1);
    
    // Phone app (position 2)
    draw_app_icon(start_x, start_y + 8,
                  " [PHN] ", "Phone",
                  COLOR_WHITE, COLOR_LIGHT_MAGENTA,
                  selected_app == 2);
    
    // Music app (position 3)
    draw_app_icon(start_x + spacing, start_y + 8,
                  " [MUS] ", "Music",
                  COLOR_WHITE, COLOR_DARK_GRAY,
                  selected_app == 3);
    
    // Instructions at bottom
    fill_box(0, VGA_HEIGHT - 2, VGA_WIDTH, 2, (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    draw_centered_text("Arrow Keys: Navigate | Enter: Open | Q: Quit", 
                      VGA_HEIGHT - 1, (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_GREEN);
}

// =============================================================================
// CALENDAR APP
// =============================================================================

static void draw_calendar_app(uint8_t scroll_pos) {
    clear_screen();
    
    // Header
    fill_box(0, 0, VGA_WIDTH, 3, (COLOR_RED << 4) | COLOR_WHITE);
    draw_centered_text("Calendar - Today's Schedule", 1, (COLOR_RED << 4) | COLOR_WHITE);
    
    // Time display
    char time_str[10];
    char h[3], m[3];
    two_digit_str(g_ml.current_hour, h);
    two_digit_str(g_ml.current_minute, m);
    time_str[0] = h[0]; time_str[1] = h[1]; time_str[2] = ':';
    time_str[3] = m[0]; time_str[4] = m[1]; time_str[5] = '\0';
    draw_text(time_str, 2, 1, (COLOR_RED << 4) | COLOR_WHITE);
    
    // Legend
    draw_text("Scheduled", 10, 4, (COLOR_BLACK << 4) | COLOR_LIGHT_CYAN);
    draw_text("AI Suggest", 30, 4, (COLOR_BLACK << 4) | COLOR_YELLOW);
    
    // Event list
    int y = 6;
    for (uint8_t i = scroll_pos; i < g_event_count && y < VGA_HEIGHT - 3; i++) {
        CalendarEvent* evt = &g_events[i];
        
        // Background color based on event type
        uint8_t bg = evt->is_suggestion ? COLOR_YELLOW : COLOR_LIGHT_CYAN;
        uint8_t fg = COLOR_BLACK;
        
        fill_box(2, y, VGA_WIDTH - 4, 2, (bg << 4) | fg);
        
        // Time
        char time[10];
        char hh[3], mm[3];
        two_digit_str(evt->hour, hh);
        two_digit_str(evt->minute, mm);
        time[0] = hh[0]; time[1] = hh[1]; time[2] = ':';
        time[3] = mm[0]; time[4] = mm[1]; time[5] = '\0';
        draw_text(time, 4, y, (bg << 4) | fg);
        
        // Title
        draw_text(evt->title, 13, y, (bg << 4) | fg);
        
        // Duration
        char dur[10];
        uint_to_str(evt->duration, dur);
        draw_text(dur, VGA_WIDTH - 10, y, (bg << 4) | fg);
        draw_text("min", VGA_WIDTH - 7, y, (bg << 4) | fg);
        
        // Type indicator
        if (evt->is_suggestion) {
            draw_text("[AI]", 4, y + 1, (bg << 4) | COLOR_MAGENTA);
        } else {
            draw_text("[  ]", 4, y + 1, (bg << 4) | fg);
        }
        
        y += 3;
    }
    
    // Bottom bar
    fill_box(0, VGA_HEIGHT - 2, VGA_WIDTH, 2, (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    draw_centered_text("Up/Down: Scroll | B: Back | A: Add AI Suggestion", 
                      VGA_HEIGHT - 1, (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_GREEN);
}

// =============================================================================
// PROACTIVE SUGGESTIONS
// =============================================================================

typedef enum {
    ACTION_SILENCE_PHONE, ACTION_SET_REMINDER, ACTION_OPEN_NOTES,
    ACTION_START_TIMER, ACTION_PLAY_MUSIC, ACTION_PLAY_VIDEO,
    ACTION_STRETCH, ACTION_HYDRATE, ACTION_PREPARE_MATERIALS,
    ACTION_REVIEW_AGENDA, ACTION_CLOSE_DISTRACTIONS, ACTION_TAKE_BREAK,
    ACTION_SAVE_WORK, ACTION_SEND_UPDATE, ACTION_BREATHE
} ActionType;

typedef struct {
    ActionType action;
    const char* description;
    uint8_t priority;
    uint8_t auto_execute;
} ProactiveSuggestion;

// Suggestions database
static ProactiveSuggestion meeting_suggestions[] = {
    {ACTION_SILENCE_PHONE, "Silence phone for meeting", 90, 1},
    {ACTION_REVIEW_AGENDA, "Review meeting agenda", 80, 0},
    {ACTION_OPEN_NOTES, "Open note-taking app", 70, 0}
};

static ProactiveSuggestion lunch_suggestions[] = {
    {ACTION_SAVE_WORK, "Save work before break", 95, 1},
    {ACTION_PLAY_MUSIC, "Play: Chill Vibes playlist", 70, 0},
    {ACTION_PLAY_VIDEO, "Watch: Chef's Table S1E1", 60, 0}
};

static ProactiveSuggestion work_suggestions[] = {
    {ACTION_CLOSE_DISTRACTIONS, "Close social media", 85, 1},
    {ACTION_START_TIMER, "Start 45-min focus timer", 80, 0}
};

static ProactiveSuggestion break_suggestions[] = {
    {ACTION_STRETCH, "Stretch your legs", 70, 0},
    {ACTION_PLAY_MUSIC, "Play energizing music", 60, 0}
};

static uint8_t g_shown_suggestions[MAX_EVENTS] = {0};

// Check if string contains substring
static uint8_t str_contains(const char* str, const char* substr) {
    while (*str) {
        const char* s1 = str;
        const char* s2 = substr;
        while (*s1 && *s2 && *s1 == *s2) {
            s1++; s2++;
        }
        if (!*s2) return 1;
        str++;
    }
    return 0;
}

// Get proactive suggestion for event
static ProactiveSuggestion* get_proactive_suggestion(uint8_t event_idx, uint8_t* count) {
    if (event_idx >= g_event_count) return NULL;
    
    CalendarEvent* evt = &g_events[event_idx];
    const char* title = evt->title;
    
    if (str_contains(title, "Meeting")) {
        *count = 3;
        return meeting_suggestions;
    } else if (str_contains(title, "Lunch")) {
        *count = 3;
        return lunch_suggestions;
    } else if (str_contains(title, "Project") || str_contains(title, "Work")) {
        *count = 2;
        return work_suggestions;
    } else if (str_contains(title, "Coffee") || str_contains(title, "Break")) {
        *count = 2;
        return break_suggestions;
    }
    
    return NULL;
}

// Check for upcoming events needing proactive suggestions
static int8_t check_for_proactive_event(uint8_t current_hour, uint8_t current_minute) {
    int16_t current_mins = current_hour * 60 + current_minute;
    
    for (uint8_t i = 0; i < g_event_count; i++) {
        if (g_shown_suggestions[i]) continue;  // Already suggested
        
        CalendarEvent* evt = &g_events[i];
        int16_t event_mins = evt->hour * 60 + evt->minute;
        int16_t diff = event_mins - current_mins;
        
        // Suggest 8-10 minutes before (narrower window)
        if (diff >= 8 && diff <= 10) {
            return i;
        }
    }
    
    return -1;
}

// =============================================================================
// PROACTIVE NOTIFICATION UI
// =============================================================================

static void draw_proactive_notification(const char* event_title, 
                                       ProactiveSuggestion* suggestion,
                                       uint8_t show_actions) {
    // Notification popup (center of screen)
    int popup_y = 8;
    int popup_h = show_actions ? 10 : 8;
    
    // Semi-transparent background (dark gray)
    fill_box(10, popup_y, VGA_WIDTH - 20, popup_h, 
            (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    draw_box(10, popup_y, VGA_WIDTH - 20, popup_h,
            (COLOR_YELLOW << 4) | COLOR_BLACK);
    
    // Icon
    draw_text(" [!] ", 12, popup_y + 1, 
             (COLOR_DARK_GRAY << 4) | COLOR_YELLOW);
    
    // Title
    draw_text("PROACTIVE SUGGESTION", 20, popup_y + 1,
             (COLOR_DARK_GRAY << 4) | COLOR_YELLOW);
    
    // Event context
    draw_text("Upcoming: ", 12, popup_y + 3,
             (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_CYAN);
    draw_text(event_title, 23, popup_y + 3,
             (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    
    // Suggestion
    draw_text("Suggestion:", 12, popup_y + 5,
             (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_GREEN);
    draw_text(suggestion->description, 12, popup_y + 6,
             (COLOR_DARK_GRAY << 4) | COLOR_WHITE);
    
    if (show_actions) {
        // Action prompt
        if (suggestion->auto_execute) {
            draw_text("[AUTO] Executing... (N to cancel)", 12, popup_y + 8,
                     (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_RED);
        } else {
            draw_text("[Y] Accept  [N] Dismiss", 12, popup_y + 8,
                     (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_GREEN);
        }
    }
}

// =============================================================================
// UI STATE  (file-scope so all tasks can share it)
// =============================================================================

typedef enum {
    SCREEN_HOME,
    SCREEN_CALENDAR,
    SCREEN_AI,
    SCREEN_MEMORY,
    SCREEN_SETTINGS
} ScreenType;

static ScreenType g_current_screen   = SCREEN_HOME;
static uint8_t    g_selected_app     = 0;
static uint8_t    g_scroll_pos       = 0;
// Set to 1 by task_metrics while a proactive notification is showing.
// task_ui checks this and skips key processing so the key isn't consumed
// before task_metrics can read it.
volatile uint8_t  g_notification_active = 0;

// =============================================================================
// SCHEDULER FUNCTIONS  (task_init, scheduler_tick, yield, task_sleep,
// sched_status_str). Declarations live in kernel/scheduler.h.
// =============================================================================

sched_status_t task_init(Task *t, uint8_t priority, void (*entry)(void),
                         uint8_t *stack_buf, uint32_t stack_size) {
    if (!t || !entry || !stack_buf) return SCHED_ERR_NULL_PTR;
    if (priority >= NUM_TASKS)       return SCHED_ERR_BAD_PRIORITY;
    if (stack_size < MIN_TASK_STACK) return SCHED_ERR_STACK_TOO_SMALL;

    uint32_t *sp = (uint32_t *)(stack_buf + stack_size);
    *--sp = (uint32_t)entry;
    uint32_t *ebp_ptr = sp;
    *--sp = 0;
    for (int i = 0; i < 8; i++) *--sp = 0;
    *--sp = SCHED_EFLAGS_INIT;

    t->esp       = (uint32_t)sp;
    t->ebp       = (uint32_t)ebp_ptr;
    t->state     = TASK_READY;
    t->priority  = priority;
    t->stack_top = (uint32_t)(stack_buf + stack_size);
    t->wake_tick = 0;
    return SCHED_OK;
}

const char *sched_status_str(sched_status_t s) {
    switch (s) {
    case SCHED_OK:                  return "ok";
    case SCHED_ERR_NULL_PTR:        return "null pointer argument";
    case SCHED_ERR_BAD_PRIORITY:    return "priority out of range";
    case SCHED_ERR_STACK_TOO_SMALL: return "stack too small";
    case SCHED_ERR_BAD_STATE:       return "invalid scheduler state";
    default:                        return "unknown scheduler error";
    }
}

// Called from isr_pit (scheduler.asm) every 1 ms, and by yield()/task_sleep().
void __attribute__((used)) scheduler_tick(void) {
    g_tick++;

    for (int i = 0; i < NUM_TASKS; i++) {
        if (g_tasks[i].state == TASK_SLEEPING && g_tick >= g_tasks[i].wake_tick) {
            g_tasks[i].state = TASK_READY;
            g_ready_mask |= (uint8_t)(1 << i);
        }
    }

    int8_t best = -1;
    for (int i = 0; i < NUM_TASKS; i++) {
        if (g_tasks[i].state == TASK_READY) { best = (int8_t)i; break; }
    }
    if (best < 0) best = NUM_TASKS - 1;

    if ((uint8_t)best == g_current_task) return;

    uint8_t prev = g_current_task;
    if (g_tasks[prev].state == TASK_RUNNING) {
        g_tasks[prev].state  = TASK_READY;
        g_ready_mask |= (uint8_t)(1 << prev);
    }

    g_tasks[best].state  = TASK_RUNNING;
    g_ready_mask &= (uint8_t)~(1 << best);
    g_current_task = (uint8_t)best;

    switch_context(&g_tasks[prev], &g_tasks[best]);
}

void yield(void) {
    g_tasks[g_current_task].state = TASK_READY;
    g_ready_mask |= (uint8_t)(1 << g_current_task);
    scheduler_tick();
}

void task_sleep(uint32_t ticks) {
    uint8_t idx            = g_current_task;
    g_tasks[idx].state     = TASK_SLEEPING;
    g_tasks[idx].wake_tick = g_tick + ticks;
    g_ready_mask &= (uint8_t)~(1 << idx);
    scheduler_tick();
}

// =============================================================================
// TASK 3 — Idle Task (priority 3, lowest). HLT until next interrupt.
// =============================================================================
void task_idle(void) {
    while (1) { __asm__ volatile("hlt"); }
}

// =============================================================================
// TASK 1 — SNN Inference Engine (priority 1).
// Mirrors the reference's "every 30 (virtual) minutes" proactive add with the
// anti-repeat buffer. Polls once per second of virtual time.
// =============================================================================
void task_snn(void) {
    static uint8_t      last_suggestion_minute = 255;
    static const char  *last_3_suggestions[3]  = {NULL, NULL, NULL};
    static uint8_t      suggestion_index       = 0;

    while (1) {
        if ((g_ml.current_minute == 0 || g_ml.current_minute == 30) &&
            g_ml.current_minute != last_suggestion_minute) {
            last_suggestion_minute = g_ml.current_minute;

            int idle_mins = get_idle_minutes_until_next_event();

            if (idle_mins >= 30 || idle_mins == 0) {
                if (idle_mins == 0) idle_mins = 180;

                int activity_idx;
                const char *snn_suggestion = get_snn_suggestion_wrapper(&activity_idx);

                uint8_t is_repeat = 0;
                for (int i = 0; i < 3; i++) {
                    if (last_3_suggestions[i] == snn_suggestion) { is_repeat = 1; break; }
                }
                if (is_repeat) {
                    uint8_t saved = g_ml.engagement;
                    g_ml.engagement = (g_ml.engagement + 30) % 100;
                    snn_suggestion = get_snn_suggestion_wrapper(&activity_idx);
                    g_ml.engagement = saved;
                }

                if (g_event_count < MAX_EVENTS) {
                    uint8_t suggest_hour   = g_ml.current_hour;
                    uint8_t suggest_minute = g_ml.current_minute + 5;
                    if (suggest_minute >= 60) {
                        suggest_minute -= 60;
                        suggest_hour = (suggest_hour + 1) % 24;
                    }

                    g_events[g_event_count++] = (CalendarEvent){
                        suggest_hour, suggest_minute, 15,
                        snn_suggestion, 1, (uint8_t)(activity_idx % 6)
                    };

                    last_3_suggestions[suggestion_index % 3] = snn_suggestion;
                    suggestion_index++;

                    if (g_current_screen == SCREEN_CALENDAR) {
                        draw_calendar_app(g_scroll_pos);
                    }
                }
            }
        }

        task_sleep(1000);  // poll virtual-time gates once per real second
    }
}

// =============================================================================
// TASK 2 — System Metrics / Proactive AI (priority 2).
// Advances virtual time, runs the 8-10-min proactive notification flow, and
// drives the blink indicator.
// =============================================================================
void task_metrics(void) {
    uint32_t last_metrics_tick = 0;
    uint32_t last_blink_tick   = 0;
    uint8_t  blink_state       = 0;

    while (1) {
        if (g_tick - last_metrics_tick >= 100) {
            last_metrics_tick = g_tick;
            ml_update_context(100000, !keyboard_has_data());

            int8_t event_idx = check_for_proactive_event(
                g_ml.current_hour, g_ml.current_minute);

            if (event_idx >= 0) {
                uint8_t count = 0;
                ProactiveSuggestion *suggestions = get_proactive_suggestion(
                    (uint8_t)event_idx, &count);

                if (suggestions && count > 0) {
                    g_notification_active = 1;

                    draw_proactive_notification(
                        g_events[event_idx].title, &suggestions[0], 1);
                    draw_text(">>> NOTIFICATION ACTIVE <<<", 20, 2,
                             (COLOR_BLACK << 4) | COLOR_YELLOW);

                    g_shown_suggestions[event_idx] = 1;

                    uint32_t timeout_end = g_tick + 300000;  // 300 s
                    uint32_t last_disp   = g_tick;
                    uint8_t  responded   = 0;

                    while (!responded && g_tick < timeout_end) {
                        if (g_tick - last_disp >= 1000) {
                            last_disp = g_tick;
                            uint32_t secs_left = (timeout_end - g_tick) / 1000;
                            uint32_t mins = secs_left / 60;
                            uint32_t secs = secs_left % 60;
                            char countdown[20];
                            countdown[0]  = 'T'; countdown[1]  = 'i';
                            countdown[2]  = 'm'; countdown[3]  = 'e';
                            countdown[4]  = ':'; countdown[5]  = ' ';
                            countdown[6]  = '0' + (char)(mins / 10);
                            countdown[7]  = '0' + (char)(mins % 10);
                            countdown[8]  = ':';
                            countdown[9]  = '0' + (char)(secs / 10);
                            countdown[10] = '0' + (char)(secs % 10);
                            countdown[11] = '\0';
                            draw_text(countdown, VGA_WIDTH - 14, 16,
                                     (COLOR_DARK_GRAY << 4) | COLOR_YELLOW);
                        }

                        char key = check_key();

                        if (key == 'y') {
                            fill_box(12, 15, VGA_WIDTH - 24, 3,
                                    (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                            draw_text("Suggestion accepted!", 14, 15,
                                    (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                            draw_text("Adding to calendar...", 14, 16,
                                    (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                            task_sleep(500);

                            if (g_event_count < MAX_EVENTS) {
                                CalendarEvent *evt = &g_events[event_idx];
                                uint8_t new_hour   = evt->hour;
                                uint8_t new_minute = evt->minute;
                                if (new_minute >= 5) {
                                    new_minute -= 5;
                                } else {
                                    new_minute = new_minute + 60 - 5;
                                    new_hour = (new_hour > 0) ? new_hour - 1 : 23;
                                }

                                for (int i = (int)g_event_count; i > (int)event_idx; i--) {
                                    g_events[i] = g_events[i - 1];
                                }
                                for (int i = MAX_EVENTS - 1; i > (int)event_idx; i--) {
                                    g_shown_suggestions[i] = g_shown_suggestions[i - 1];
                                }

                                g_events[event_idx].hour          = new_hour;
                                g_events[event_idx].minute        = new_minute;
                                g_events[event_idx].duration      = 5;
                                g_events[event_idx].title         = suggestions[0].description;
                                g_events[event_idx].is_suggestion = 1;
                                g_events[event_idx].category      = 7;
                                g_shown_suggestions[event_idx]        = 1;
                                g_shown_suggestions[event_idx + 1]    = 1;
                                g_event_count++;

                                fill_box(12, 15, VGA_WIDTH - 24, 2,
                                        (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                                draw_text("Added to calendar!", 14, 15,
                                        (COLOR_LIGHT_GREEN << 4) | COLOR_WHITE);
                                task_sleep(500);
                            } else {
                                fill_box(12, 15, VGA_WIDTH - 24, 2,
                                        (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                                draw_text("Calendar full!", 14, 15,
                                        (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                                task_sleep(300);
                            }
                            responded = 1;

                        } else if (key == 'n') {
                            fill_box(12, 15, VGA_WIDTH - 24, 2,
                                    (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                            draw_text("Suggestion dismissed", 14, 15,
                                    (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                            task_sleep(300);
                            responded = 1;
                        }

                        if (!responded) task_sleep(100);
                    }

                    g_notification_active = 0;

                    if (g_current_screen == SCREEN_HOME) {
                        draw_home_screen(g_selected_app);
                    } else if (g_current_screen == SCREEN_CALENDAR) {
                        draw_calendar_app(g_scroll_pos);
                    }
                }
            }
        }

        if (g_tick - last_blink_tick >= 500) {
            last_blink_tick = g_tick;
            blink_state ^= 1;
            if (blink_state) {
                putchar_at('*', VGA_WIDTH - 1, VGA_HEIGHT - 1,
                          (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
            } else {
                putchar_at(' ', VGA_WIDTH - 1, VGA_HEIGHT - 1,
                          (COLOR_BLACK << 4) | COLOR_BLACK);
            }
        }

        yield();
    }
}

// =============================================================================
// TASK 0 — UI / Input Handler (priority 0, highest).
// Mirrors the reference's keyboard handling for home + calendar screens.
// =============================================================================
void task_ui(void) {
    while (1) {
        if (g_notification_active) {
            yield();
            continue;
        }

        char key = check_key();
        if (key) {
            if (g_current_screen == SCREEN_HOME) {
                if (key == 'w' || key == 'i') {
                    if (g_selected_app >= 2) g_selected_app -= 2;
                    draw_home_screen(g_selected_app);
                } else if (key == 's' || key == 'k') {
                    if (g_selected_app < 2) g_selected_app += 2;
                    draw_home_screen(g_selected_app);
                } else if (key == 'a' || key == 'j') {
                    if (g_selected_app % 2 == 1) g_selected_app--;
                    draw_home_screen(g_selected_app);
                } else if (key == 'd' || key == 'l') {
                    if (g_selected_app % 2 == 0) g_selected_app++;
                    draw_home_screen(g_selected_app);
                } else if (key == '\n' || key == ' ') {
                    if (g_selected_app == 0) {
                        g_current_screen = SCREEN_CALENDAR;
                        g_scroll_pos = 0;
                        draw_calendar_app(g_scroll_pos);
                    }
                }
            } else if (g_current_screen == SCREEN_CALENDAR) {
                if (key == 'w' || key == 'i') {
                    if (g_scroll_pos > 0) g_scroll_pos--;
                    draw_calendar_app(g_scroll_pos);
                } else if (key == 's' || key == 'k') {
                    if (g_scroll_pos < g_event_count - 1) g_scroll_pos++;
                    draw_calendar_app(g_scroll_pos);
                } else if (key == 'b' || key == 'q') {
                    g_current_screen = SCREEN_HOME;
                    draw_home_screen(g_selected_app);
                } else if (key == 'a') {
                    int activity_idx;
                    const char *snn_suggestion = get_snn_suggestion_wrapper(&activity_idx);
                    if (g_event_count < MAX_EVENTS) {
                        uint8_t next_hour = (g_ml.current_hour + 1) % 24;
                        g_events[g_event_count++] = (CalendarEvent){
                            next_hour, 0, 15,
                            snn_suggestion, 1, (uint8_t)(activity_idx % 6)
                        };
                        draw_calendar_app(g_scroll_pos);
                    }
                }
            }
        }

        yield();
    }
}

// =============================================================================
// KERNEL MAIN — initialise hardware and scheduler, then hand off to task 0.
// =============================================================================
void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr;
    if (magic != 0x2BADB002) return;

    // ── ML / Calendar initialisation ───────────────────────────────────────
    g_ml.energy_level   = 80;
    g_ml.engagement     = 50;
    g_ml.current_hour   = 8;    // Start at 8:30 AM
    g_ml.current_minute = 30;
    g_ml.day_of_week    = 0;    // Monday
    g_ml.cycles         = 510000000;   // 8 h 30 min × 1M cycles/min

    init_calendar();

    // ── Interrupt controller and timer ─────────────────────────────────────
    idt_install();   // load IDT with isr_pit at vector 0x20
    pic_remap();     // remap PIC: IRQ0 → 0x20, unmask IRQ0 only
    pit_init();      // configure PIT channel 0 for 1000 Hz

    // ── Task initialisation ────────────────────────────────────────────────
    task_init(&g_tasks[0], 0, task_ui,      g_task_stacks[0], TASK_STACK_SZ);
    task_init(&g_tasks[1], 1, task_snn,     g_task_stacks[1], TASK_STACK_SZ);
    task_init(&g_tasks[2], 2, task_metrics, g_task_stacks[2], TASK_STACK_SZ);
    task_init(&g_tasks[3], 3, task_idle,    g_task_stacks[3], TASK_STACK_SZ);

    g_ready_mask = 0x0F;   // all four tasks start READY

    // ── Initial screen draw ────────────────────────────────────────────────
    draw_home_screen(g_selected_app);

    // ── Bootstrap: hand control to task 0. ─────────────────────────────────
    g_tasks[0].state = TASK_RUNNING;
    g_ready_mask    &= ~(uint8_t)0x01;
    g_current_task   = 0;

    // Dummy TCB absorbs the save of kernel_main's frame. Never re-scheduled.
    static Task dummy_task;
    switch_context(&dummy_task, &g_tasks[0]);

    __asm__ volatile("cli; hlt");   // unreachable
}

