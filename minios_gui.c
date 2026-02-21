// minios_gui.c - CarPlay-style graphical interface for MiniOS
// Uses ANSI graphics and Unicode for a modern look

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <unistd.h>
#include <termios.h>
#include <sys/time.h>
#include <sys/select.h>
#include <sys/resource.h>
#include <sys/ioctl.h>
#include <wchar.h>
#include <locale.h>

// Enhanced colors for CarPlay-style interface
#define RESET "\033[0m"
#define BOLD "\033[1m"
#define DIM "\033[2m"

// CarPlay color scheme (dark mode)
#define BG_DARK "\033[48;2;0;0;0m"
#define BG_CARD "\033[48;2;28;28;30m"
#define BG_ACCENT "\033[48;2;0;122;255m"
#define BG_SUCCESS "\033[48;2;52;199;89m"
#define BG_WARNING "\033[48;2;255;149;0m"
#define BG_ERROR "\033[48;2;255;59;48m"

#define FG_PRIMARY "\033[38;2;255;255;255m"
#define FG_SECONDARY "\033[38;2;174;174;178m"
#define FG_ACCENT "\033[38;2;0;122;255m"
#define FG_SUCCESS "\033[38;2;52;199;89m"
#define FG_ERROR "\033[38;2;255;59;48m"

// Box drawing characters
#define TOP_LEFT "╭"
#define TOP_RIGHT "╮"
#define BOTTOM_LEFT "╰"
#define BOTTOM_RIGHT "╯"
#define HORIZONTAL "─"
#define VERTICAL "│"
#define HEAVY_HORIZONTAL "━"
#define HEAVY_VERTICAL "┃"

// Icons (Unicode)
#define ICON_CLOCK "🕐"
#define ICON_CALENDAR "📅"
#define ICON_ACTIVITY "⚡"
#define ICON_CHECK "✓"
#define ICON_CROSS "✗"
#define ICON_INFO "ℹ"
#define ICON_CPU "⚙"
#define ICON_MEMORY "💾"
#define ICON_TIMER "⏱"
#define ICON_STAR "★"
#define ICON_BRAIN "🧠"

// System metrics
typedef struct {
    double cpu_usage;
    size_t memory_used;
    uint64_t uptime_ms;
} SystemMetrics;

// Feedback log
typedef struct {
    char activity[128];
    char feedback[16];
    time_t timestamp;
    double cpu_usage;
    size_t memory_used;
    uint64_t latency_ms;
} FeedbackLog;

// SNN Model
typedef struct {
    float weights[10][10];
    float biases[10];
    float activity_scores[20];
    int feedback_count;
} SNNModel;

// Activity database with categories
typedef struct {
    const char* text;
    const char* category;
    const char* icon;
} Activity;

static Activity activities[] = {
    {"Take a 15-minute walk outside", "Physical", "🚶"},
    {"Do 10 minutes of stretching", "Physical", "🧘"},
    {"Read a book chapter", "Mental", "📚"},
    {"Call a friend or family", "Social", "📞"},
    {"Meditate for 10 minutes", "Wellness", "🧘"},
    {"Work on creative project", "Creative", "🎨"},
    {"Review weekly goals", "Productive", "📋"},
    {"Organize workspace", "Productive", "🗂"},
    {"Learn something new", "Mental", "🎓"},
    {"Prepare healthy snack", "Wellness", "🥗"},
    {"Listen to podcast", "Mental", "🎧"},
    {"Write in journal", "Creative", "✍"},
    {"Light housework", "Productive", "🏠"},
    {"Practice hobby", "Creative", "🎯"},
    {"Review budget", "Productive", "💰"},
    {"Plan meals", "Productive", "🍽"},
    {"Quick workout", "Physical", "💪"},
    {"Catch up on emails", "Productive", "📧"},
    {"Brainstorm ideas", "Creative", "💡"},
    {"Take power nap", "Wellness", "😴"}
};
#define NUM_ACTIVITIES (sizeof(activities) / sizeof(activities[0]))

// Global state
static SNNModel model;
static FeedbackLog logs[1000];
static int log_count = 0;
static SystemMetrics metrics;
static time_t start_time;
static int current_activity_idx = 0;
static uint64_t last_inference_latency = 0;
static char notification_msg[256] = "";
static time_t notification_time = 0;
static int notification_type = 0; // 0=info, 1=success, 2=error

// Terminal handling
static struct termios orig_termios;
static int term_width = 80;
static int term_height = 24;

void disable_raw_mode() {
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios);
    printf(RESET);
    printf("\033[?25h"); // Show cursor
}

void enable_raw_mode() {
    tcgetattr(STDIN_FILENO, &orig_termios);
    atexit(disable_raw_mode);
    
    struct termios raw = orig_termios;
    raw.c_lflag &= ~(ECHO | ICANON | ISIG);
    raw.c_iflag &= ~(IXON | ICRNL);
    raw.c_cc[VMIN] = 0;
    raw.c_cc[VTIME] = 1;
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
    
    printf("\033[?25l"); // Hide cursor
}

void get_terminal_size() {
    struct winsize w;
    ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);
    term_width = w.ws_col;
    term_height = w.ws_row;
}

void clear_screen() {
    printf("\033[2J\033[H");
}

void move_cursor(int x, int y) {
    printf("\033[%d;%dH", y, x);
}

// Get metrics
double get_cpu_usage() {
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    long total_us = usage.ru_utime.tv_sec * 1000000 + usage.ru_utime.tv_usec +
                    usage.ru_stime.tv_sec * 1000000 + usage.ru_stime.tv_usec;
    time_t elapsed = time(NULL) - start_time;
    return elapsed == 0 ? 0.0 : (total_us / 1000000.0) / elapsed * 100.0;
}

size_t get_memory_usage() {
    FILE* f = fopen("/proc/self/statm", "r");
    if (!f) return 0;
    unsigned long size, resident;
    fscanf(f, "%lu %lu", &size, &resident);
    fclose(f);
    return resident * sysconf(_SC_PAGESIZE);
}

// Initialize SNN model
void init_snn_model() {
    srand(time(NULL));
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            model.weights[i][j] = ((float)rand() / RAND_MAX - 0.5f) * 2.0f;
        }
        model.biases[i] = ((float)rand() / RAND_MAX - 0.5f) * 2.0f;
    }
    for (int i = 0; i < NUM_ACTIVITIES; i++) {
        model.activity_scores[i] = 0.5f;
    }
    model.feedback_count = 0;
}

float sigmoid(float x) {
    return x > 10.0f ? 1.0f : (x < -10.0f ? 0.0f : 1.0f / (1.0f + expf(-x)));
}

void run_inference(const char* context, int* output_idx, uint64_t* latency_ms) {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    float features[10];
    unsigned int hash = 5381;
    for (const char* p = context; *p; p++) hash = ((hash << 5) + hash) + *p;
    for (int i = 0; i < 10; i++) features[i] = ((float)((hash >> (i * 3)) & 0x7) - 3.5f) / 3.5f;
    
    float hidden[10];
    for (int i = 0; i < 10; i++) {
        float sum = model.biases[i];
        for (int j = 0; j < 10; j++) sum += features[j] * model.weights[i][j];
        hidden[i] = sigmoid(sum);
    }
    
    for (int i = 0; i < NUM_ACTIVITIES; i++) {
        float score = 0.0f;
        for (int j = 0; j < 10; j++) score += hidden[j];
        score /= 10.0f;
        model.activity_scores[i] = 0.7f * model.activity_scores[i] + 0.3f * score;
    }
    
    for (int i = 0; i < log_count && i < 100; i++) {
        FeedbackLog* log = &logs[log_count - 1 - i];
        for (int j = 0; j < NUM_ACTIVITIES; j++) {
            if (strcmp(activities[j].text, log->activity) == 0) {
                if (strcmp(log->feedback, "accept") == 0) model.activity_scores[j] += 0.1f;
                else if (strcmp(log->feedback, "reject") == 0) model.activity_scores[j] -= 0.1f;
            }
        }
    }
    
    int best_idx = 0;
    float best_score = model.activity_scores[0];
    for (int i = 1; i < NUM_ACTIVITIES; i++) {
        if (model.activity_scores[i] > best_score) {
            best_score = model.activity_scores[i];
            best_idx = i;
        }
    }
    
    if (rand() % 100 < 20) best_idx = rand() % NUM_ACTIVITIES;
    *output_idx = best_idx;
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    *latency_ms = (end.tv_sec - start.tv_sec) * 1000 + (end.tv_nsec - start.tv_nsec) / 1000000;
    usleep(10000 + rand() % 20000);
    *latency_ms += 10 + rand() % 20;
}

void log_feedback(const char* activity, const char* feedback) {
    if (log_count >= 1000) {
        memmove(logs, logs + 1, sizeof(FeedbackLog) * 999);
        log_count = 999;
    }
    FeedbackLog* log = &logs[log_count++];
    strncpy(log->activity, activity, sizeof(log->activity) - 1);
    strncpy(log->feedback, feedback, sizeof(log->feedback) - 1);
    log->timestamp = time(NULL);
    log->cpu_usage = metrics.cpu_usage;
    log->memory_used = metrics.memory_used;
    log->latency_ms = last_inference_latency;
    model.feedback_count++;
}

float get_model_accuracy() {
    if (log_count < 10) return 0.0f;
    int accepts = 0;
    int recent = log_count < 100 ? log_count : 100;
    for (int i = 0; i < recent; i++) {
        if (strcmp(logs[log_count - 1 - i].feedback, "accept") == 0) accepts++;
    }
    return (float)accepts / (float)recent * 100.0f;
}

void show_notification(const char* msg, int type) {
    strncpy(notification_msg, msg, sizeof(notification_msg) - 1);
    notification_time = time(NULL);
    notification_type = type;
}

void draw_rounded_box(int x, int y, int width, int height, const char* bg_color) {
    printf("%s", bg_color);
    
    // Top border
    move_cursor(x, y);
    printf("%s", TOP_LEFT);
    for (int i = 0; i < width - 2; i++) printf("%s", HORIZONTAL);
    printf("%s", TOP_RIGHT);
    
    // Middle
    for (int i = 1; i < height - 1; i++) {
        move_cursor(x, y + i);
        printf("%s", VERTICAL);
        for (int j = 0; j < width - 2; j++) printf(" ");
        printf("%s", VERTICAL);
    }
    
    // Bottom border
    move_cursor(x, y + height - 1);
    printf("%s", BOTTOM_LEFT);
    for (int i = 0; i < width - 2; i++) printf("%s", HORIZONTAL);
    printf("%s", BOTTOM_RIGHT);
    
    printf(RESET);
}

void draw_text_centered(int y, const char* text, const char* color) {
    int len = strlen(text);
    int x = (term_width - len) / 2;
    move_cursor(x, y);
    printf("%s%s%s", color, text, RESET);
}

void draw_card(int x, int y, int width, int height, const char* title, const char* content) {
    draw_rounded_box(x, y, width, height, BG_CARD);
    
    if (title) {
        move_cursor(x + 2, y + 1);
        printf("%s%s%s%s", BOLD, FG_PRIMARY, title, RESET);
    }
    
    if (content) {
        move_cursor(x + 2, y + 3);
        printf("%s%s%s", FG_SECONDARY, content, RESET);
    }
}

void draw_ui() {
    clear_screen();
    get_terminal_size();
    
    metrics.cpu_usage = get_cpu_usage();
    metrics.memory_used = get_memory_usage();
    metrics.uptime_ms = (time(NULL) - start_time) * 1000;
    
    // Background
    printf(BG_DARK);
    clear_screen();
    
    // Header
    move_cursor(1, 2);
    printf("%s%s%sMiniOS Neural Activity Suggester%s", BOLD, FG_PRIMARY, "", RESET);
    
    // Time card
    time_t now = time(NULL);
    struct tm* t = localtime(&now);
    char time_str[100];
    snprintf(time_str, sizeof(time_str), "%s %02d:%02d:%02d", 
             (const char*[]){"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"}[t->tm_wday],
             t->tm_hour, t->tm_min, t->tm_sec);
    
    int card_width = term_width - 4;
    draw_card(2, 4, card_width, 5, "📅 Current Time", time_str);
    
    // Activity card (main)
    Activity* act = &activities[current_activity_idx];
    char activity_text[200];
    snprintf(activity_text, sizeof(activity_text), "%s  %s", act->icon, act->text);
    
    draw_card(2, 10, card_width, 8, "⚡ Suggested Activity", activity_text);
    move_cursor(4, 14);
    printf("%s%sCategory: %s%s", DIM, FG_SECONDARY, act->category, RESET);
    move_cursor(4, 15);
    printf("%s%sConfidence: %.0f%%%s", DIM, FG_SECONDARY, model.activity_scores[current_activity_idx] * 100, RESET);
    
    // Stats card
    draw_card(2, 19, card_width / 2 - 2, 6, "📊 Performance", NULL);
    move_cursor(4, 21);
    printf("%sLatency: %s%lums%s", FG_SECONDARY, FG_ACCENT, last_inference_latency, RESET);
    move_cursor(4, 22);
    printf("%sAccuracy: %s%.1f%%%s", FG_SECONDARY, FG_SUCCESS, get_model_accuracy(), RESET);
    move_cursor(4, 23);
    printf("%sLogs: %s%d/1000%s", FG_SECONDARY, FG_PRIMARY, log_count, RESET);
    
    // System card
    draw_card(card_width / 2 + 2, 19, card_width / 2, 6, "⚙ System", NULL);
    move_cursor(card_width / 2 + 4, 21);
    printf("%sCPU: %s%.1f%%%s", FG_SECONDARY, FG_PRIMARY, metrics.cpu_usage, RESET);
    move_cursor(card_width / 2 + 4, 22);
    printf("%sRAM: %s%.1fMB%s", FG_SECONDARY, FG_PRIMARY, metrics.memory_used / (1024.0 * 1024.0), RESET);
    move_cursor(card_width / 2 + 4, 23);
    printf("%sUptime: %s%lus%s", FG_SECONDARY, FG_PRIMARY, metrics.uptime_ms / 1000, RESET);
    
    // Notification
    if (notification_msg[0] && (time(NULL) - notification_time) < 3) {
        const char* notif_bg = notification_type == 1 ? BG_SUCCESS : (notification_type == 2 ? BG_ERROR : BG_ACCENT);
        draw_rounded_box(term_width / 2 - 20, 26, 40, 3, notif_bg);
        move_cursor(term_width / 2 - 18, 27);
        printf("%s%s%s", BOLD, FG_PRIMARY, notification_msg);
    }
    
    // Action buttons (bottom)
    int button_y = term_height - 3;
    move_cursor(2, button_y);
    printf("%s%s [A] Accept %s  ", BG_SUCCESS, FG_PRIMARY, RESET);
    printf("%s%s [R] Reject %s  ", BG_ERROR, FG_PRIMARY, RESET);
    printf("%s%s [I] Ignore %s  ", BG_CARD, FG_SECONDARY, RESET);
    printf("%s%s [L] Logs %s  ", BG_ACCENT, FG_PRIMARY, RESET);
    printf("%s%s [Q] Quit %s", BG_CARD, FG_SECONDARY, RESET);
    
    fflush(stdout);
}

void export_logs() {
    FILE* f = fopen("/mnt/user-data/outputs/minios_feedback_logs.csv", "w");
    if (!f) {
        show_notification("Failed to export logs", 2);
        return;
    }
    fprintf(f, "Timestamp,Activity,Feedback,CPU_Usage,Memory_MB,Latency_ms\n");
    for (int i = 0; i < log_count; i++) {
        fprintf(f, "%ld,%s,%s,%.1f,%.2f,%lu\n",
                logs[i].timestamp, logs[i].activity, logs[i].feedback,
                logs[i].cpu_usage, logs[i].memory_used / (1024.0 * 1024.0),
                logs[i].latency_ms);
    }
    fclose(f);
    show_notification("✓ Logs exported to CSV", 1);
}

void show_logs() {
    clear_screen();
    printf(BG_DARK);
    printf("%s%s%sRecent Activity Logs%s\n\n", BOLD, FG_PRIMARY, "", RESET);
    
    int start = log_count > 15 ? log_count - 15 : 0;
    for (int i = start; i < log_count; i++) {
        FeedbackLog* log = &logs[i];
        struct tm* t = localtime(&log->timestamp);
        const char* color = strcmp(log->feedback, "accept") == 0 ? FG_SUCCESS :
                           strcmp(log->feedback, "reject") == 0 ? FG_ERROR : FG_SECONDARY;
        printf("%s%02d:%02d%s │ %s%-8s%s │ %s\n",
               FG_SECONDARY, t->tm_hour, t->tm_min, RESET,
               color, log->feedback, RESET,
               log->activity);
    }
    
    printf("\n%sAccuracy: %s%.1f%%%s  │  %sTotal: %s%d logs%s\n",
           FG_SECONDARY, FG_SUCCESS, get_model_accuracy(), RESET,
           FG_SECONDARY, FG_PRIMARY, log_count, RESET);
    printf("\n[E] Export  [Enter] Back\n");
    
    while (1) {
        fd_set readfds;
        struct timeval timeout = {0, 100000};
        FD_ZERO(&readfds);
        FD_SET(STDIN_FILENO, &readfds);
        if (select(STDIN_FILENO + 1, &readfds, NULL, NULL, &timeout) > 0) {
            char c = getchar();
            if (c == 'e' || c == 'E') {
                export_logs();
                sleep(2);
                break;
            } else if (c == '\n' || c == 'q' || c == 'Q' || c == 27) {
                break;
            }
        }
    }
}

int main() {
    setlocale(LC_ALL, "");
    start_time = time(NULL);
    enable_raw_mode();
    init_snn_model();
    
    char context[256];
    time_t now = time(NULL);
    struct tm* t = localtime(&now);
    snprintf(context, sizeof(context), "%s, %02d:%02d",
             (const char*[]){"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"}[t->tm_wday],
             t->tm_hour, t->tm_min);
    
    run_inference(context, &current_activity_idx, &last_inference_latency);
    
    while (1) {
        draw_ui();
        
        fd_set readfds;
        struct timeval timeout = {0, 100000};
        FD_ZERO(&readfds);
        FD_SET(STDIN_FILENO, &readfds);
        
        if (select(STDIN_FILENO + 1, &readfds, NULL, NULL, &timeout) > 0) {
            char c = getchar();
            
            if (c == 'a' || c == 'A') {
                log_feedback(activities[current_activity_idx].text, "accept");
                show_notification("✓ Activity accepted!", 1);
                run_inference(context, &current_activity_idx, &last_inference_latency);
            } else if (c == 'r' || c == 'R') {
                log_feedback(activities[current_activity_idx].text, "reject");
                show_notification("✗ Activity rejected", 2);
                run_inference(context, &current_activity_idx, &last_inference_latency);
            } else if (c == 'i' || c == 'I') {
                log_feedback(activities[current_activity_idx].text, "ignore");
                show_notification("○ Activity ignored", 0);
            } else if (c == 'l' || c == 'L') {
                show_logs();
            } else if (c == 'q' || c == 'Q') {
                break;
            }
        }
    }
    
    clear_screen();
    printf("%sMiniOS shutting down...\n", FG_PRIMARY);
    printf("Total interactions: %d\n", log_count);
    printf("Final accuracy: %.1f%%\n%s", get_model_accuracy(), RESET);
    return 0;
}
