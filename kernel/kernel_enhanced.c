// kernel_enhanced.c - Bootable kernel with proactive ML and memory tracking
// Works in both QEMU and VirtualBox

#include <stdint.h>
#include <stddef.h>

// =============================================================================
// INLINE PROACTIVE ML (SIMPLIFIED FOR KERNEL)
// =============================================================================

// Simplified context for kernel space
typedef struct {
    uint32_t cycles;
    uint8_t time_segment;        // 0=morning, 1=afternoon, 2=evening, 3=night
    uint8_t energy_level;        // 0-100
    uint8_t engagement;          // 0-100
    uint32_t idle_cycles;
    uint32_t total_accepts;
    uint32_t total_rejects;
    uint8_t activity_prefs[20];  // Preference score per activity
} MLContext;

static MLContext g_ml = {0};

// Activity database (20 activities)
typedef struct {
    const char* desc;
    uint8_t category;    // 0=physical, 1=mental, 2=social, etc.
    uint8_t energy_req;  // 0-100
    uint8_t time_pref;   // 0-3 (morning/afternoon/evening/any)
} Activity;

static Activity g_activities[] = {
    // Physical
    {"Take a 15-minute walk outside", 0, 60, 0},
    {"Do 10 minutes of stretching", 0, 40, 0},
    {"Quick 5-minute workout", 0, 80, 0},
    // Mental
    {"Review your weekly goals", 1, 50, 0},
    {"Plan tomorrow's tasks", 1, 40, 1},
    {"Practice a new skill", 1, 60, 1},
    // Social
    {"Call a friend or family", 2, 50, 2},
    {"Send a thoughtful message", 2, 30, 3},
    {"Schedule coffee with colleague", 2, 40, 1},
    // Productive
    {"Organize your workspace", 3, 50, 0},
    {"Clear your email inbox", 3, 45, 1},
    {"Update your to-do list", 3, 35, 3},
    // Creative
    {"Work on creative project", 4, 70, 3},
    {"Journal for 10 minutes", 4, 30, 2},
    {"Brainstorm new ideas", 4, 60, 1},
    // Wellness
    {"Practice mindfulness meditation", 5, 20, 2},
    {"Take a few deep breaths", 5, 10, 3},
    {"Read a chapter from book", 5, 25, 2},
    // Learning
    {"Watch educational video", 6, 35, 1},
    {"Read article about something new", 6, 40, 1}
};
#define NUM_ACTIVITIES 20

// Update ML context
static void ml_update_context(uint32_t cycles, uint8_t idle) {
    g_ml.cycles += cycles;
    
    // Estimate time segment from cycles (crude approximation)
    uint32_t minutes = (g_ml.cycles / 1000000) % (24 * 60);
    uint32_t hour = (minutes / 60) % 24;
    
    if (hour >= 6 && hour < 12) g_ml.time_segment = 0;
    else if (hour >= 12 && hour < 17) g_ml.time_segment = 1;
    else if (hour >= 17 && hour < 22) g_ml.time_segment = 2;
    else g_ml.time_segment = 3;
    
    // Energy based on time
    const uint8_t energy_by_time[] = {80, 70, 50, 30};
    g_ml.energy_level = energy_by_time[g_ml.time_segment];
    
    // Update engagement
    uint32_t total = g_ml.total_accepts + g_ml.total_rejects;
    if (total > 0) {
        g_ml.engagement = (g_ml.total_accepts * 100) / total;
    } else {
        g_ml.engagement = 50;
    }
    
    if (idle) g_ml.idle_cycles += cycles;
    
    mem_track_context_update();
}

// Score an activity
static uint8_t ml_score_activity(uint8_t idx) {
    if (idx >= NUM_ACTIVITIES) return 0;
    
    Activity* act = &g_activities[idx];
    uint8_t score = 0;
    
    // Time match (30 points)
    if (act->time_pref == 3) {
        score += 20;
    } else if (act->time_pref == g_ml.time_segment) {
        score += 30;
    } else {
        score += 5;
    }
    
    // Energy match (30 points)
    int diff = act->energy_req - g_ml.energy_level;
    if (diff < 0) diff = -diff;
    if (diff < 15) score += 30;
    else if (diff < 30) score += 20;
    else score += 5;
    
    // Preference (20 points)
    score += (g_ml.activity_prefs[idx] * 2);
    
    // Engagement bonus (10 points)
    if (g_ml.engagement > 50) score += 10;
    
    return score;
}

// Select best activity
static uint8_t ml_suggest_activity(void) {
    uint8_t best = 0;
    uint8_t best_score = 0;
    
    for (uint8_t i = 0; i < NUM_ACTIVITIES; i++) {
        uint8_t score = ml_score_activity(i);
        if (score > best_score) {
            best_score = score;
            best = i;
        }
    }
    
    return best;
}

// Record feedback
static void ml_record_feedback(uint8_t idx, uint8_t accepted) {
    if (accepted) {
        g_ml.total_accepts++;
        if (idx < 20 && g_ml.activity_prefs[idx] < 10) {
            g_ml.activity_prefs[idx]++;
        }
    } else {
        g_ml.total_rejects++;
        if (idx < 20 && g_ml.activity_prefs[idx] > 0) {
            g_ml.activity_prefs[idx]--;
        }
    }
    g_ml.idle_cycles = 0;
    mem_track_var_change();
}

// Should suggest?
static uint8_t ml_should_suggest(void) {
    return (g_ml.idle_cycles > 30000000 && g_ml.engagement > 20);
}

// =============================================================================
// INLINE MEMORY TRACKING (SIMPLIFIED FOR KERNEL)
// =============================================================================

typedef struct {
    uint32_t vga_updates;      // VGA buffer updates
    uint32_t context_updates;  // ML context updates
    uint32_t total_writes;     // All memory writes
    uint32_t variable_changes; // Variable modifications
    uint32_t peak_usage;       // Peak memory "usage" proxy
} MemStats;

static MemStats g_mem = {0};

static void mem_track_vga_write(void) {
    g_mem.vga_updates++;
    g_mem.total_writes++;
}

static void mem_track_context_update(void) {
    g_mem.context_updates++;
    g_mem.total_writes++;
}

static void mem_track_var_change(void) {
    g_mem.variable_changes++;
    g_mem.total_writes++;
}

// =============================================================================
// VGA & GUI CODE
// =============================================================================

#define VGA_MEMORY 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

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
#define COLOR_DARK_GRAY 0x8

static uint16_t* const vga = (uint16_t*)VGA_MEMORY;
static uint8_t current_color = 0x0F;

static size_t strlen(const char* str) {
    size_t len = 0;
    while (str[len]) len++;
    return len;
}

static void set_color(uint8_t fg, uint8_t bg) {
    current_color = (bg << 4) | fg;
}

static void putchar_at(char c, int x, int y, uint8_t color) {
    if (x >= 0 && x < VGA_WIDTH && y >= 0 && y < VGA_HEIGHT) {
        vga[y * VGA_WIDTH + x] = ((uint16_t)color << 8) | c;
        mem_track_vga_write();
    }
}

static void clear_screen(void) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga[i] = ((uint16_t)current_color << 8) | ' ';
    }
    mem_track_vga_write();
}

static void draw_box(int x, int y, int w, int h, uint8_t color) {
    for (int i = 0; i < w; i++) {
        char c = (i == 0) ? 201 : (i == w-1) ? 187 : 205;
        putchar_at(c, x + i, y, color);
    }
    for (int i = 0; i < w; i++) {
        char c = (i == 0) ? 200 : (i == w-1) ? 188 : 205;
        putchar_at(c, x + i, y + h - 1, color);
    }
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

// Simple number to string
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
    // Reverse
    for (int j = 0; j < i/2; j++) {
        char t = buf[j];
        buf[j] = buf[i-1-j];
        buf[i-1-j] = t;
    }
}

// =============================================================================
// KEYBOARD POLLING
// =============================================================================

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

static int keyboard_has_data(void) {
    return (inb(0x64) & 0x01) != 0;
}

static char scancode_to_char(uint8_t sc) {
    switch (sc) {
        case 0x1E: return 'a';
        case 0x13: return 'r';
        case 0x31: return 'n';
        default: return 0;
    }
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
// ENHANCED GUI
// =============================================================================

static void draw_enhanced_gui(uint8_t activity_idx, uint8_t show_context) {
    clear_screen();
    
    // Header
    set_color(COLOR_YELLOW, COLOR_BLUE);
    for (int i = 0; i < VGA_WIDTH; i++) {
        for (int j = 0; j < 3; j++) {
            putchar_at(' ', i, j, current_color);
        }
    }
    draw_centered_text("MiniOS Enhanced - Proactive AI System", 1, current_color);
    
    // Activity panel
    set_color(COLOR_WHITE, COLOR_CYAN);
    draw_box(2, 4, VGA_WIDTH - 4, 10, current_color);
    
    set_color(COLOR_YELLOW, COLOR_CYAN);
    if (show_context) {
        draw_text("Proactive Suggestion:", 4, 5, current_color);
    } else {
        draw_text("Suggested Activity:", 4, 5, current_color);
    }
    
    // Activity text
    set_color(COLOR_WHITE, COLOR_CYAN);
    draw_text(g_activities[activity_idx].desc, 4, 7, (COLOR_CYAN << 4) | COLOR_LIGHT_GREEN);
    
    // Context info
    if (show_context) {
        set_color(COLOR_LIGHT_CYAN, COLOR_CYAN);
        const char* times[] = {"Morning", "Afternoon", "Evening", "Night"};
        draw_text("Context: ", 4, 9, current_color);
        draw_text(times[g_ml.time_segment], 14, 9, current_color);
        
        char buf[16];
        draw_text("Energy: ", 4, 10, current_color);
        uint_to_str(g_ml.energy_level, buf);
        draw_text(buf, 13, 10, current_color);
        draw_text("%", 16, 10, current_color);
        
        draw_text("Engagement: ", 4, 11, current_color);
        uint_to_str(g_ml.engagement, buf);
        draw_text(buf, 17, 11, current_color);
        draw_text("%", 20, 11, current_color);
    }
    
    // Controls
    set_color(COLOR_LIGHT_CYAN, COLOR_CYAN);
    draw_text("[A] Accept  [R] Reject  [N] Next", 4, 12, current_color);
    
    // Memory stats panel
    set_color(COLOR_WHITE, COLOR_MAGENTA);
    draw_box(2, 15, 38, 6, current_color);
    draw_text("Memory Tracking:", 4, 16, current_color);
    
    char buf[16];
    draw_text("VGA: ", 4, 17, current_color);
    uint_to_str(g_mem.vga_updates, buf);
    draw_text(buf, 10, 17, current_color);
    
    draw_text("Context: ", 4, 18, current_color);
    uint_to_str(g_mem.context_updates, buf);
    draw_text(buf, 14, 18, current_color);
    
    draw_text("Changes: ", 4, 19, current_color);
    uint_to_str(g_mem.variable_changes, buf);
    draw_text(buf, 14, 19, current_color);
    
    // ML stats panel
    set_color(COLOR_WHITE, COLOR_DARK_GRAY);
    draw_box(42, 15, 36, 6, current_color);
    draw_text("ML Statistics:", 44, 16, current_color);
    
    draw_text("Accepts: ", 44, 17, current_color);
    uint_to_str(g_ml.total_accepts, buf);
    draw_text(buf, 54, 17, current_color);
    
    draw_text("Rejects: ", 44, 18, current_color);
    uint_to_str(g_ml.total_rejects, buf);
    draw_text(buf, 54, 18, current_color);
    
    // Status bar
    set_color(COLOR_LIGHT_GREEN, COLOR_BLACK);
    for (int i = 0; i < VGA_WIDTH; i++) {
        putchar_at(' ', i, VGA_HEIGHT - 1, current_color);
    }
    draw_text(" MiniOS Enhanced | Proactive AI + Memory Tracking", 0, VGA_HEIGHT - 1, current_color);
}

// =============================================================================
// MAIN KERNEL
// =============================================================================

void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr;
    
    if (magic != 0x2BADB002) return;
    
    // Initialize
    g_ml.energy_level = 80;
    g_ml.engagement = 50;
    
    uint8_t current_activity = 0;
    uint8_t suggestion_pending = 0;
    uint32_t cycle_count = 0;
    
    draw_enhanced_gui(current_activity, 1);
    
    while (1) {
        cycle_count++;
        
        // Update context periodically
        if (cycle_count % 10000 == 0) {
            ml_update_context(10000, !keyboard_has_data());
        }
        
        // Proactive suggestion
        if (!suggestion_pending && ml_should_suggest()) {
            current_activity = ml_suggest_activity();
            draw_enhanced_gui(current_activity, 1);
            suggestion_pending = 1;
        }
        
        // Handle input
        char key = check_key();
        if (key) {
            if (key == 'a') {
                if (suggestion_pending) {
                    ml_record_feedback(current_activity, 1);
                    suggestion_pending = 0;
                }
                set_color(COLOR_BLACK, COLOR_LIGHT_GREEN);
                draw_box(25, 8, 30, 3, current_color);
                draw_text("Activity Accepted!", 27, 9, current_color);
                for (volatile int i = 0; i < 5000000; i++);
                current_activity = ml_suggest_activity();
                draw_enhanced_gui(current_activity, 1);
                suggestion_pending = 1;
            } else if (key == 'r') {
                if (suggestion_pending) {
                    ml_record_feedback(current_activity, 0);
                    suggestion_pending = 0;
                }
                set_color(COLOR_WHITE, COLOR_LIGHT_RED);
                draw_box(25, 8, 30, 3, current_color);
                draw_text("Activity Rejected", 27, 9, current_color);
                for (volatile int i = 0; i < 5000000; i++);
                current_activity = ml_suggest_activity();
                draw_enhanced_gui(current_activity, 1);
                suggestion_pending = 1;
            } else if (key == 'n') {
                current_activity = ml_suggest_activity();
                draw_enhanced_gui(current_activity, 1);
                suggestion_pending = 1;
            }
        }
        
        // Blink indicator
        if ((cycle_count / 100000) % 2 == 0) {
            putchar_at('*', VGA_WIDTH - 1, VGA_HEIGHT - 1, 
                      (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
        } else {
            putchar_at(' ', VGA_WIDTH - 1, VGA_HEIGHT - 1, 
                      (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
        }
    }
}
