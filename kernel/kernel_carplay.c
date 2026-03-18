// kernel_carplay.c - CarPlay-style interface with app launcher and calendar
// Works in QEMU and VirtualBox with proactive ML and memory tracking

#include <stdint.h>
#include <stddef.h>

// Use Case Neuromorphic SNN (replaces old ML system)
#include "usecase_snn_weights.h"

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
    
    const uint8_t energy[] = {80, 70, 50, 30};
    g_ml.energy_level = energy[g_ml.time_segment];
    
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
    return (idle_mins > 0 && idle_mins < 240) ? idle_mins : 0;  // Max 4 hours
}

// Get neuromorphic SNN suggestion
static const char* get_snn_suggestion_wrapper(int* out_activity_idx) {
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
    
    // Get SNN suggestion (using renamed function to avoid conflict)
    const char* suggestion = get_snn_proactive_suggestion(
        g_ml.current_hour,
        g_ml.current_minute,
        g_ml.day_of_week,
        g_ml.energy_level,
        g_ml.engagement,
        idle_mins,
        has_meeting,
        (g_ml.total_accepts > 10) ? 10 : g_ml.total_accepts,
        (g_ml.total_rejects > 10) ? 10 : g_ml.total_rejects
    );
    
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
    
    // AI Suggestions app (position 1)
    draw_app_icon(start_x + spacing, start_y,
                  " [AI] ", "Suggester",
                  COLOR_WHITE, COLOR_LIGHT_BLUE,
                  selected_app == 1);
    
    // Memory app (position 2)
    draw_app_icon(start_x, start_y + 8,
                  " [MEM] ", "Memory",
                  COLOR_WHITE, COLOR_LIGHT_MAGENTA,
                  selected_app == 2);
    
    // Settings app (position 3)
    draw_app_icon(start_x + spacing, start_y + 8,
                  " [SET] ", "Settings",
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

typedef enum {
    SCREEN_HOME,
    SCREEN_CALENDAR,
    SCREEN_AI,
    SCREEN_MEMORY,
    SCREEN_SETTINGS
} ScreenType;

void kernel_main(uint32_t magic, uint32_t addr) {
    (void)addr;
    if (magic != 0x2BADB002) return;
    
    // Initialize
    g_ml.energy_level = 80;
    g_ml.engagement = 50;
    g_ml.current_hour = 8;      // Start at 8:30 AM
    g_ml.current_minute = 30;   // 30 min before first event
    g_ml.day_of_week = 0;       // Monday (0=Mon, 6=Sun)
    
    // IMPORTANT: Initialize cycles to match 8:30 AM on Monday
    // 8:30 AM = (8 * 60 + 30) = 510 minutes from midnight
    // 510 minutes * 1,000,000 cycles/minute = 510,000,000 cycles
    g_ml.cycles = 510000000;
    
    init_calendar();
    
    ScreenType current_screen = SCREEN_HOME;
    uint8_t selected_app = 0;
    uint8_t scroll_pos = 0;
    uint32_t cycle_count = 0;
    
    draw_home_screen(selected_app);
    
    while (1) {
        cycle_count++;
        
        // Update context
        if (cycle_count % 10000 == 0) {
            ml_update_context(10000, !keyboard_has_data());
            
            // Check for proactive suggestions (on ALL screens!)
            int8_t event_idx = check_for_proactive_event(
                g_ml.current_hour, 
                g_ml.current_minute
            );
            
            if (event_idx >= 0) {
                // Found an event needing proactive suggestion!
                uint8_t count;
                ProactiveSuggestion* suggestions = get_proactive_suggestion(event_idx, &count);
                
                if (suggestions && count > 0) {
                    // Remember which screen we were on
                    ScreenType previous_screen = current_screen;
                    
                    // FORCE REDRAW of notification (overlays current screen)
                    // Draw notification directly without checking anything
                    draw_proactive_notification(
                        g_events[event_idx].title,
                        &suggestions[0],
                        1  // show actions
                    );
                    
                    // Show a visible marker that we're in notification mode
                    draw_text(">>> NOTIFICATION ACTIVE <<<", 20, 2,
                             (COLOR_BLACK << 4) | COLOR_YELLOW);
                    
                    g_shown_suggestions[event_idx] = 1;
                    
                    // Wait for user response or timeout (5 MINUTES = 300 seconds)
                    volatile uint32_t timeout_counter = 0;
                    uint8_t responded = 0;
                    const uint32_t timeout_limit = 300000000;  // 300 seconds * 1M cycles
                    
                    while (!responded && timeout_counter < timeout_limit) {
                        timeout_counter++;
                        
                        // Update countdown every ~1 second (1M cycles)
                        if (timeout_counter % 1000000 == 0) {
                            uint32_t seconds_left = 300 - (timeout_counter / 1000000);
                            if (seconds_left > 0) {
                                // Convert to minutes:seconds
                                uint32_t mins = seconds_left / 60;
                                uint32_t secs = seconds_left % 60;
                                
                                char countdown[30];
                                countdown[0] = 'T';
                                countdown[1] = 'i';
                                countdown[2] = 'm';
                                countdown[3] = 'e';
                                countdown[4] = ' ';
                                countdown[5] = 'l';
                                countdown[6] = 'e';
                                countdown[7] = 'f';
                                countdown[8] = 't';
                                countdown[9] = ':';
                                countdown[10] = ' ';
                                countdown[11] = '0' + (mins / 10);
                                countdown[12] = '0' + (mins % 10);
                                countdown[13] = ':';
                                countdown[14] = '0' + (secs / 10);
                                countdown[15] = '0' + (secs % 10);
                                countdown[16] = '\0';
                                
                                draw_text(countdown, VGA_WIDTH - 25, 16,
                                         (COLOR_DARK_GRAY << 4) | COLOR_YELLOW);
                            }
                        }
                        
                        char key = check_key();
                        
                        if (key == 'y') {
                            // ACCEPT - Add suggestion to calendar!
                            
                            // Show confirmation
                            fill_box(12, 15, VGA_WIDTH - 24, 3,
                                    (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                            draw_text("Suggestion accepted!", 14, 15,
                                    (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                            draw_text("Adding to calendar...", 14, 16,
                                    (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                            
                            // Wait to show message
                            for (volatile int i = 0; i < 5000000; i++);
                            
                            // Add the suggestion to calendar
                            if (g_event_count < MAX_EVENTS) {
                                CalendarEvent* evt = &g_events[event_idx];
                                
                                // Create new calendar entry based on the suggestion
                                // Calculate time 5 minutes BEFORE the event
                                uint8_t new_hour = evt->hour;
                                uint8_t new_minute = evt->minute;
                                
                                // Subtract 5 minutes properly
                                if (new_minute >= 5) {
                                    new_minute -= 5;
                                } else {
                                    // Need to borrow from hour
                                    new_minute = new_minute + 60 - 5;
                                    if (new_hour > 0) {
                                        new_hour -= 1;
                                    } else {
                                        new_hour = 23;  // Wrap to previous day
                                    }
                                }
                                
                                // INSERT suggestion BEFORE the original event
                                // Shift all events from event_idx forward by one
                                for (int i = g_event_count; i > event_idx; i--) {
                                    g_events[i] = g_events[i - 1];
                                }
                                
                                // ALSO shift the shown_suggestions tracking array!
                                for (int i = MAX_EVENTS - 1; i > event_idx; i--) {
                                    g_shown_suggestions[i] = g_shown_suggestions[i - 1];
                                }
                                
                                // Insert at position event_idx (before the original event)
                                g_events[event_idx].hour = new_hour;
                                g_events[event_idx].minute = new_minute;
                                g_events[event_idx].duration = 5;
                                g_events[event_idx].title = suggestions[0].description;
                                g_events[event_idx].is_suggestion = 1;  // Mark as AI suggestion
                                g_events[event_idx].category = 7;  // Proactive action
                                
                                // Mark this NEW suggestion as shown (it shouldn't trigger again)
                                g_shown_suggestions[event_idx] = 1;
                                // Mark the NEXT position (original event) as shown too
                                g_shown_suggestions[event_idx + 1] = 1;
                                
                                g_event_count++;
                                
                                // Show success
                                fill_box(12, 15, VGA_WIDTH - 24, 2,
                                        (COLOR_LIGHT_GREEN << 4) | COLOR_BLACK);
                                draw_text("Added to calendar!", 14, 15,
                                        (COLOR_LIGHT_GREEN << 4) | COLOR_WHITE);
                                for (volatile int i = 0; i < 5000000; i++);
                            } else {
                                // Calendar full
                                fill_box(12, 15, VGA_WIDTH - 24, 2,
                                        (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                                draw_text("Calendar full!", 14, 15,
                                        (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                                for (volatile int i = 0; i < 3000000; i++);
                            }
                            
                            responded = 1;
                            
                        } else if (key == 'n') {
                            // REJECT - Don't add to calendar
                            
                            fill_box(12, 15, VGA_WIDTH - 24, 2,
                                    (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                            draw_text("Suggestion dismissed", 14, 15,
                                    (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
                            for (volatile int i = 0; i < 3000000; i++);
                            
                            responded = 1;
                        }
                    }
                    
                    // Redraw whatever screen we were on
                    if (previous_screen == SCREEN_HOME) {
                        draw_home_screen(selected_app);
                    } else if (previous_screen == SCREEN_CALENDAR) {
                        draw_calendar_app(scroll_pos);
                    }
                    // Add more screens here as they're implemented
                }
            }
        }
        
        // Handle input
        char key = check_key();
        if (key) {
            if (current_screen == SCREEN_HOME) {
                // Home screen navigation
                if (key == 'w' || key == 'i') {  // Up
                    if (selected_app >= 2) selected_app -= 2;
                    draw_home_screen(selected_app);
                } else if (key == 's' || key == 'k') {  // Down
                    if (selected_app < 2) selected_app += 2;
                    draw_home_screen(selected_app);
                } else if (key == 'a' || key == 'j') {  // Left
                    if (selected_app % 2 == 1) selected_app--;
                    draw_home_screen(selected_app);
                } else if (key == 'd' || key == 'l') {  // Right
                    if (selected_app % 2 == 0) selected_app++;
                    draw_home_screen(selected_app);
                } else if (key == '\n' || key == ' ') {  // Enter
                    if (selected_app == 0) {
                        current_screen = SCREEN_CALENDAR;
                        scroll_pos = 0;
                        draw_calendar_app(scroll_pos);
                    }
                }
            } else if (current_screen == SCREEN_CALENDAR) {
                // Calendar navigation
                if (key == 'w' || key == 'i') {  // Scroll up
                    if (scroll_pos > 0) scroll_pos--;
                    draw_calendar_app(scroll_pos);
                } else if (key == 's' || key == 'k') {  // Scroll down
                    if (scroll_pos < g_event_count - 1) scroll_pos++;
                    draw_calendar_app(scroll_pos);
                } else if (key == 'b' || key == 'q') {  // Back
                    current_screen = SCREEN_HOME;
                    draw_home_screen(selected_app);
                } else if (key == 'a') {  // Add AI suggestion
                    // Use neuromorphic SNN for suggestion
                    int activity_idx;
                    const char* snn_suggestion = get_snn_suggestion_wrapper(&activity_idx);
                    
                    // Add to calendar with SNN suggestion text
                    if (g_event_count < MAX_EVENTS) {
                        uint8_t next_hour = (g_ml.current_hour + 1) % 24;
                        
                        g_events[g_event_count++] = (CalendarEvent){
                            next_hour,
                            0,
                            15,
                            snn_suggestion,  // Use SNN suggestion directly
                            1,  // Is AI suggestion
                            activity_idx % 6  // Map to category
                        };
                        
                        draw_calendar_app(scroll_pos);
                    }
                }
            }
        }
        
        // =====================================================================
        // FULLY PROACTIVE: Check for idle time every 15 minutes and suggest!
        // =====================================================================
        static uint8_t last_suggestion_minute = 255;  // Track when we last suggested
        
        // Check every 15 minutes (on the quarter hour: 0, 15, 30, 45)
        if (g_ml.current_minute % 15 == 0 && g_ml.current_minute != last_suggestion_minute) {
            last_suggestion_minute = g_ml.current_minute;
            
            // Calculate idle time
            int idle_mins = get_idle_minutes_until_next_event();
            
            // PROACTIVE: If there's at least 15 minutes free, suggest something!
            if (idle_mins >= 15 || idle_mins == 0) {  // 0 means no events = lots of free time!
                // If no events at all, assume 3 hours free
                if (idle_mins == 0) idle_mins = 180;
                
                // Get neuromorphic SNN suggestion
                int activity_idx;
                const char* snn_suggestion = get_snn_suggestion_wrapper(&activity_idx);
                
                // Add proactive suggestion to calendar
                if (g_event_count < MAX_EVENTS) {
                    // Add at current time + 5 minutes
                    uint8_t suggest_hour = g_ml.current_hour;
                    uint8_t suggest_minute = g_ml.current_minute + 5;
                    
                    if (suggest_minute >= 60) {
                        suggest_minute -= 60;
                        suggest_hour = (suggest_hour + 1) % 24;
                    }
                    
                    // Add to calendar
                    g_events[g_event_count++] = (CalendarEvent){
                        suggest_hour,
                        suggest_minute,
                        15,  // 15 minute duration
                        snn_suggestion,
                        1,  // Is AI suggestion
                        activity_idx % 6
                    };
                    
                    // If on calendar screen, refresh it
                    if (current_screen == SCREEN_CALENDAR) {
                        draw_calendar_app(scroll_pos);
                    }
                }
            }
        }
        
        // Blink indicator
        if ((cycle_count / 100000) % 2 == 0) {
            putchar_at('*', VGA_WIDTH - 1, VGA_HEIGHT - 1, 
                      (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
        } else {
            putchar_at(' ', VGA_WIDTH - 1, VGA_HEIGHT - 1, 
                      (COLOR_BLACK << 4) | COLOR_BLACK);
        }
    }
}
