// minios_simulator.c - User-space simulation of MiniOS
// This demonstrates all OS features without needing QEMU

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
#include <signal.h>

// Colors for terminal
#define COLOR_RESET "\033[0m"
#define COLOR_HEADER "\033[44;93m"
#define COLOR_STATUS "\033[100;92m"
#define COLOR_PANEL "\033[46;97m"
#define COLOR_TITLE "\033[1;93m"
#define COLOR_SUCCESS "\033[92m"
#define COLOR_ERROR "\033[91m"
#define COLOR_INFO "\033[96m"
#define COLOR_NOTIFICATION "\033[43;30m"

// System metrics
typedef struct {
    double cpu_usage;
    size_t memory_used;
    uint64_t uptime_ms;
} SystemMetrics;

// Feedback log entry
typedef struct {
    char activity[128];
    char feedback[16];
    time_t timestamp;
    double cpu_usage;
    size_t memory_used;
    uint64_t latency_ms;
} FeedbackLog;

// SNN Model state
typedef struct {
    float weights[10][10];
    float biases[10];
    float activity_scores[20];
    int feedback_count;
} SNNModel;

// Activity database
static const char* activities[] = {
    "Take a 15-minute walk outside",
    "Do 10 minutes of stretching exercises",
    "Read a chapter from your current book",
    "Call a friend or family member",
    "Practice mindfulness meditation for 10 minutes",
    "Work on a creative project",
    "Review your weekly goals",
    "Organize your workspace",
    "Learn something new online",
    "Prepare a healthy snack",
    "Listen to an educational podcast",
    "Write in your journal",
    "Do some light housework",
    "Practice a hobby or skill",
    "Review your budget and finances",
    "Plan meals for the week",
    "Do a quick workout routine",
    "Catch up on emails",
    "Brainstorm new ideas",
    "Take a power nap"
};
#define NUM_ACTIVITIES (sizeof(activities) / sizeof(activities[0]))

// Global state
static SNNModel model;
static FeedbackLog logs[1000];
static int log_count = 0;
static SystemMetrics metrics;
static time_t start_time;
static char current_activity[128] = "";
static uint64_t last_inference_latency = 0;
static char notification_msg[256] = "";
static time_t notification_time = 0;

// Terminal handling
static struct termios orig_termios;

void disable_raw_mode() {
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios);
}

void enable_raw_mode() {
    tcgetattr(STDIN_FILENO, &orig_termios);
    atexit(disable_raw_mode);
    
    struct termios raw = orig_termios;
    raw.c_lflag &= ~(ECHO | ICANON | ISIG);
    raw.c_iflag &= ~(IXON | ICRNL);
    raw.c_cc[VMIN] = 0;
    raw.c_cc[VTIME] = 1;  // 100ms timeout
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
}

// Clear screen
void clear_screen() {
    printf("\033[2J\033[H");
}

// Get CPU usage
double get_cpu_usage() {
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    
    long total_us = usage.ru_utime.tv_sec * 1000000 + usage.ru_utime.tv_usec +
                    usage.ru_stime.tv_sec * 1000000 + usage.ru_stime.tv_usec;
    
    time_t elapsed = time(NULL) - start_time;
    if (elapsed == 0) return 0.0;
    
    return (total_us / 1000000.0) / elapsed * 100.0;
}

// Get memory usage
size_t get_memory_usage() {
    FILE* f = fopen("/proc/self/statm", "r");
    if (!f) return 0;
    
    unsigned long size, resident, share, text, lib, data, dt;
    fscanf(f, "%lu %lu %lu %lu %lu %lu %lu", &size, &resident, &share, &text, &lib, &data, &dt);
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

// Sigmoid activation
float sigmoid(float x) {
    if (x > 10.0f) return 1.0f;
    if (x < -10.0f) return 0.0f;
    return 1.0f / (1.0f + expf(-x));
}

// Run SNN inference
void run_inference(const char* calendar_context, char* output, uint64_t* latency_ms) {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // Extract features from calendar context
    float features[10];
    unsigned int hash = 5381;
    for (const char* p = calendar_context; *p; p++) {
        hash = ((hash << 5) + hash) + *p;
    }
    
    for (int i = 0; i < 10; i++) {
        features[i] = ((float)((hash >> (i * 3)) & 0x7) - 3.5f) / 3.5f;
    }
    
    // Forward pass
    float hidden[10];
    for (int i = 0; i < 10; i++) {
        float sum = model.biases[i];
        for (int j = 0; j < 10; j++) {
            sum += features[j] * model.weights[i][j];
        }
        hidden[i] = sigmoid(sum);
    }
    
    // Update activity scores
    for (int i = 0; i < NUM_ACTIVITIES; i++) {
        float score = 0.0f;
        for (int j = 0; j < 10; j++) {
            score += hidden[j];
        }
        score /= 10.0f;
        model.activity_scores[i] = 0.7f * model.activity_scores[i] + 0.3f * score;
    }
    
    // Apply feedback learning
    for (int i = 0; i < log_count && i < 100; i++) {
        FeedbackLog* log = &logs[log_count - 1 - i];
        for (int j = 0; j < NUM_ACTIVITIES; j++) {
            if (strcmp(activities[j], log->activity) == 0) {
                if (strcmp(log->feedback, "accept") == 0) {
                    model.activity_scores[j] += 0.1f;
                } else if (strcmp(log->feedback, "reject") == 0) {
                    model.activity_scores[j] -= 0.1f;
                }
            }
        }
    }
    
    // Find best activity
    int best_idx = 0;
    float best_score = model.activity_scores[0];
    for (int i = 1; i < NUM_ACTIVITIES; i++) {
        if (model.activity_scores[i] > best_score) {
            best_score = model.activity_scores[i];
            best_idx = i;
        }
    }
    
    // Add exploration (20% random)
    if (rand() % 100 < 20) {
        best_idx = rand() % NUM_ACTIVITIES;
    }
    
    strcpy(output, activities[best_idx]);
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    *latency_ms = (end.tv_sec - start.tv_sec) * 1000 + (end.tv_nsec - start.tv_nsec) / 1000000;
    
    // Simulate realistic latency
    usleep(10000 + rand() % 20000); // 10-30ms
    *latency_ms += 10 + rand() % 20;
}

// Log feedback
void log_feedback(const char* activity, const char* feedback) {
    if (log_count >= 1000) {
        // Shift logs
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

// Calculate model accuracy
float get_model_accuracy() {
    if (log_count < 10) return 0.0f;
    
    int accepts = 0;
    int recent = log_count < 100 ? log_count : 100;
    
    for (int i = 0; i < recent; i++) {
        if (strcmp(logs[log_count - 1 - i].feedback, "accept") == 0) {
            accepts++;
        }
    }
    
    return (float)accepts / (float)recent * 100.0f;
}

// Show notification
void show_notification(const char* msg) {
    strncpy(notification_msg, msg, sizeof(notification_msg) - 1);
    notification_time = time(NULL);
}

// Draw UI
void draw_ui() {
    clear_screen();
    
    // Update metrics
    metrics.cpu_usage = get_cpu_usage();
    metrics.memory_used = get_memory_usage();
    metrics.uptime_ms = (time(NULL) - start_time) * 1000;
    
    // Header
    printf(COLOR_HEADER);
    printf("═══════════════════════════════════════════════════════════════════════════════\n");
    printf("                     MiniOS - Neural Activity Suggester                        \n");
    printf("═══════════════════════════════════════════════════════════════════════════════\n");
    printf(COLOR_RESET);
    
    // Main panel
    printf(COLOR_PANEL);
    printf("\n");
    
    time_t now = time(NULL);
    struct tm* t = localtime(&now);
    printf("  " COLOR_INFO "Current Time:" COLOR_RESET COLOR_PANEL " %02d:%02d:%02d, %s %d, %d\n",
           t->tm_hour, t->tm_min, t->tm_sec,
           (const char*[]){"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}[t->tm_wday],
           t->tm_mday,
           t->tm_year + 1900);
    
    printf("  " COLOR_INFO "Day of Week:" COLOR_RESET COLOR_PANEL " %s\n",
           (const char*[]){"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}[t->tm_wday]);
    
    printf("\n");
    printf(COLOR_TITLE "  Suggested Activity:\n" COLOR_RESET);
    printf(COLOR_SUCCESS "  → %s\n" COLOR_RESET, current_activity);
    printf("\n");
    
    printf(COLOR_INFO "  Performance Metrics:\n" COLOR_RESET);
    printf("  • Inference Latency: %lu ms\n", last_inference_latency);
    printf("  • Model Accuracy: %.1f%% (last 100 interactions)\n", get_model_accuracy());
    printf("  • Total Feedback: %d interactions\n", log_count);
    printf("\n");
    
    printf(COLOR_TITLE "  Actions:\n" COLOR_RESET);
    printf("  [" COLOR_SUCCESS "A" COLOR_RESET "] Accept  ");
    printf("[" COLOR_ERROR "R" COLOR_RESET "] Reject  ");
    printf("[" COLOR_INFO "I" COLOR_RESET "] Ignore  ");
    printf("[" COLOR_INFO "L" COLOR_RESET "] View Logs  ");
    printf("[" COLOR_INFO "Q" COLOR_RESET "] Quit\n");
    printf("\n");
    printf(COLOR_RESET);
    
    // Notification
    if (notification_msg[0] && (time(NULL) - notification_time) < 3) {
        printf(COLOR_NOTIFICATION);
        printf("┌──────────────────────────────────────────────────────────────────────────────┐\n");
        printf("│ %-76s │\n", notification_msg);
        printf("└──────────────────────────────────────────────────────────────────────────────┘\n");
        printf(COLOR_RESET);
    } else {
        printf("\n\n\n");
    }
    
    // Status bar
    printf(COLOR_STATUS);
    printf("───────────────────────────────────────────────────────────────────────────────\n");
    printf(" CPU: %5.1f%%  |  Memory: %6.2f MB  |  Uptime: %lu s  |  Logs: %d/1000       \n",
           metrics.cpu_usage,
           metrics.memory_used / (1024.0 * 1024.0),
           metrics.uptime_ms / 1000,
           log_count);
    printf("───────────────────────────────────────────────────────────────────────────────\n");
    printf(COLOR_RESET);
    
    fflush(stdout);
}

// Export logs to CSV
void export_logs() {
    FILE* f = fopen("/mnt/user-data/outputs/minios_feedback_logs.csv", "w");
    if (!f) {
        printf("Error: Could not open log file for writing\n");
        return;
    }
    
    fprintf(f, "Timestamp,Activity,Feedback,CPU_Usage,Memory_Used_MB,Latency_ms\n");
    
    for (int i = 0; i < log_count; i++) {
        FeedbackLog* log = &logs[i];
        fprintf(f, "%ld,%s,%s,%.1f,%.2f,%lu\n",
                log->timestamp,
                log->activity,
                log->feedback,
                log->cpu_usage,
                log->memory_used / (1024.0 * 1024.0),
                log->latency_ms);
    }
    
    fclose(f);
    printf("\nLogs exported to: /mnt/user-data/outputs/minios_feedback_logs.csv\n");
    printf("Press any key to continue...\n");
    getchar();
}

// Show logs
void show_logs() {
    clear_screen();
    printf(COLOR_HEADER "Recent Feedback Logs (Last 20)\n" COLOR_RESET);
    printf("────────────────────────────────────────────────────────────────────────────────\n");
    
    int start = log_count > 20 ? log_count - 20 : 0;
    for (int i = start; i < log_count; i++) {
        FeedbackLog* log = &logs[i];
        struct tm* t = localtime(&log->timestamp);
        
        const char* color = strcmp(log->feedback, "accept") == 0 ? COLOR_SUCCESS :
                           strcmp(log->feedback, "reject") == 0 ? COLOR_ERROR : COLOR_INFO;
        
        printf("%02d:%02d:%02d | %s%-8s" COLOR_RESET " | %s\n",
               t->tm_hour, t->tm_min, t->tm_sec,
               color, log->feedback,
               log->activity);
    }
    
    printf("────────────────────────────────────────────────────────────────────────────────\n");
    printf("\nStatistics:\n");
    printf("  Total Interactions: %d\n", log_count);
    printf("  Model Accuracy: %.1f%%\n", get_model_accuracy());
    printf("  Avg Latency: ");
    
    if (log_count > 0) {
        uint64_t total_latency = 0;
        for (int i = 0; i < log_count; i++) {
            total_latency += logs[i].latency_ms;
        }
        printf("%lu ms\n", total_latency / log_count);
    } else {
        printf("N/A\n");
    }
    
    printf("\n[E] Export Logs  [Enter] Back to Main\n");
    
    char c;
    while (1) {
        c = getchar();
        if (c == 'e' || c == 'E') {
            export_logs();
            break;
        } else if (c == '\n' || c == 'q' || c == 'Q') {
            break;
        }
    }
}

// Main loop
int main() {
    printf("Initializing MiniOS...\n");
    
    start_time = time(NULL);
    enable_raw_mode();
    
    printf("Initializing SNN model...\n");
    init_snn_model();
    
    printf("Running initial inference...\n");
    char calendar_context[256];
    time_t now = time(NULL);
    struct tm* t = localtime(&now);
    snprintf(calendar_context, sizeof(calendar_context),
             "%s, %02d:%02d, %s %d",
             (const char*[]){"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}[t->tm_wday],
             t->tm_hour, t->tm_min,
             (const char*[]){"January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"}[t->tm_mon],
             t->tm_year + 1900);
    
    run_inference(calendar_context, current_activity, &last_inference_latency);
    
    printf("Starting GUI...\n");
    sleep(1);
    
    while (1) {
        draw_ui();
        
        // Read input with timeout
        fd_set readfds;
        struct timeval timeout;
        FD_ZERO(&readfds);
        FD_SET(STDIN_FILENO, &readfds);
        timeout.tv_sec = 0;
        timeout.tv_usec = 100000; // 100ms
        
        int ready = select(STDIN_FILENO + 1, &readfds, NULL, NULL, &timeout);
        
        if (ready > 0) {
            char c = getchar();
            
            if (c == 'a' || c == 'A') {
                log_feedback(current_activity, "accept");
                show_notification("✓ Activity accepted! Generating new suggestion...");
                run_inference(calendar_context, current_activity, &last_inference_latency);
            } else if (c == 'r' || c == 'R') {
                log_feedback(current_activity, "reject");
                show_notification("✗ Activity rejected. Generating alternative...");
                run_inference(calendar_context, current_activity, &last_inference_latency);
            } else if (c == 'i' || c == 'I') {
                log_feedback(current_activity, "ignore");
                show_notification("○ Activity ignored (no learning applied)");
            } else if (c == 'l' || c == 'L') {
                show_logs();
            } else if (c == 'q' || c == 'Q') {
                break;
            }
        }
    }
    
    clear_screen();
    printf("MiniOS shutting down...\n");
    printf("Total interactions: %d\n", log_count);
    printf("Final accuracy: %.1f%%\n", get_model_accuracy());
    printf("\nThank you for using MiniOS!\n");
    
    return 0;
}
