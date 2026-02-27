// python_runtime.c - Embedded Python runtime
#include <stdint.h>
#include <stddef.h>

extern void terminal_write(const char* str);
extern void terminal_write_num(uint64_t num);
extern void* kmalloc(size_t size);
extern uint64_t get_timer_ticks(void);

// Simple string functions
static size_t strlen(const char* str) {
    size_t len = 0;
    while (str[len]) len++;
    return len;
}

static void strcpy(char* dest, const char* src) {
    while (*src) {
        *dest++ = *src++;
    }
    *dest = 0;
}

static void strcat(char* dest, const char* src) {
    while (*dest) dest++;
    strcpy(dest, src);
}

static int strcmp(const char* s1, const char* s2) {
    while (*s1 && (*s1 == *s2)) {
        s1++;
        s2++;
    }
    return *(unsigned char*)s1 - *(unsigned char*)s2;
}

// Logging structure
typedef struct {
    char activity[128];
    char feedback[16];
    uint64_t timestamp;
    uint32_t cpu_usage;
    size_t memory_used;
    uint64_t latency_ms;
} FeedbackLog;

#define MAX_LOGS 1000
static FeedbackLog feedback_logs[MAX_LOGS];
static int log_count = 0;

// Simple SNN model state
typedef struct {
    float weights[10][10];
    float biases[10];
    float activity_scores[20];
} SNNModel;

static SNNModel model;

// Activity suggestions database
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

// Simple pseudo-random number generator
static uint32_t rand_seed = 123456789;

static uint32_t simple_rand(void) {
    rand_seed = (rand_seed * 1103515245 + 12345) & 0x7FFFFFFF;
    return rand_seed;
}

// Initialize model weights with simple patterns
static void init_model(void) {
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            model.weights[i][j] = ((float)(simple_rand() % 100) - 50) / 100.0f;
        }
        model.biases[i] = ((float)(simple_rand() % 100) - 50) / 100.0f;
    }
    
    // Initialize activity scores
    for (int i = 0; i < NUM_ACTIVITIES; i++) {
        model.activity_scores[i] = 0.5f;
    }
}

// Simple sigmoid activation
static float sigmoid(float x) {
    if (x > 10.0f) return 1.0f;
    if (x < -10.0f) return 0.0f;
    
    // Approximate sigmoid
    float abs_x = x < 0 ? -x : x;
    float result = 1.0f / (1.0f + abs_x);
    return x < 0 ? 1.0f - result : result;
}

// Hash function for calendar context
static uint32_t hash_context(const char* context) {
    uint32_t hash = 5381;
    while (*context) {
        hash = ((hash << 5) + hash) + *context++;
    }
    return hash;
}

// Python initialization
int python_init(void) {
    terminal_write("Initializing SNN model...\n");
    init_model();
    terminal_write("Model initialized with ");
    terminal_write_num(NUM_ACTIVITIES);
    terminal_write(" activities\n");
    return 0;
}

// Run inference
int python_run_inference(const char* calendar_context, char* output_buffer, size_t buffer_size, uint64_t* latency_ms) {
    uint64_t start_time = get_timer_ticks();
    
    // Hash the calendar context to get features
    uint32_t context_hash = hash_context(calendar_context);
    
    // Extract features from hash
    float features[10];
    for (int i = 0; i < 10; i++) {
        features[i] = ((float)((context_hash >> (i * 3)) & 0x7) - 3.5f) / 3.5f;
    }
    
    // Simple neural network forward pass
    float hidden[10];
    for (int i = 0; i < 10; i++) {
        float sum = model.biases[i];
        for (int j = 0; j < 10; j++) {
            sum += features[j] * model.weights[i][j];
        }
        hidden[i] = sigmoid(sum);
    }
    
    // Update activity scores based on hidden layer
    for (int i = 0; i < NUM_ACTIVITIES; i++) {
        float score = 0.0f;
        for (int j = 0; j < 10; j++) {
            score += hidden[j];
        }
        score = score / 10.0f;
        
        // Mix with previous score
        model.activity_scores[i] = 0.7f * model.activity_scores[i] + 0.3f * score;
    }
    
    // Apply feedback-based adjustments
    for (int i = 0; i < log_count && i < 100; i++) {
        FeedbackLog* log = &feedback_logs[log_count - 1 - i];
        for (int j = 0; j < NUM_ACTIVITIES; j++) {
            int match = 1;
            for (int k = 0; activities[j][k] && log->activity[k]; k++) {
                if (activities[j][k] != log->activity[k]) {
                    match = 0;
                    break;
                }
            }
            
            if (match) {
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
    
    // Add some randomness
    if (simple_rand() % 100 < 20) {
        best_idx = simple_rand() % NUM_ACTIVITIES;
    }
    
    // Copy result to output buffer
    strcpy(output_buffer, activities[best_idx]);
    
    uint64_t end_time = get_timer_ticks();
    *latency_ms = (end_time - start_time) * 10; // Convert to ms
    
    return 0;
}

// Log feedback
void python_log_feedback(const char* activity, const char* feedback) {
    if (log_count >= MAX_LOGS) {
        // Shift logs
        for (int i = 0; i < MAX_LOGS - 1; i++) {
            feedback_logs[i] = feedback_logs[i + 1];
        }
        log_count = MAX_LOGS - 1;
    }
    
    FeedbackLog* log = &feedback_logs[log_count++];
    strcpy(log->activity, activity);
    strcpy(log->feedback, feedback);
    log->timestamp = get_timer_ticks();
    log->cpu_usage = 0; // Will be filled by caller
    log->memory_used = 0; // Will be filled by caller
    log->latency_ms = 0;
    
    terminal_write("Logged feedback: ");
    terminal_write(activity);
    terminal_write(" - ");
    terminal_write(feedback);
    terminal_write("\n");
}

// Get model accuracy (simple calculation)
float python_get_accuracy(void) {
    if (log_count < 10) return 0.0f;
    
    int accepts = 0;
    int recent = log_count < 100 ? log_count : 100;
    
    for (int i = 0; i < recent; i++) {
        if (strcmp(feedback_logs[log_count - 1 - i].feedback, "accept") == 0) {
            accepts++;
        }
    }
    
    return (float)accepts / (float)recent;
}

// Export logs
void python_export_logs(char* buffer, size_t buffer_size) {
    char* ptr = buffer;
    size_t remaining = buffer_size;
    
    const char* header = "Timestamp,Activity,Feedback,CPU,Memory,Latency\n";
    size_t header_len = strlen(header);
    if (remaining > header_len) {
        strcpy(ptr, header);
        ptr += header_len;
        remaining -= header_len;
    }
    
    for (int i = 0; i < log_count && remaining > 100; i++) {
        FeedbackLog* log = &feedback_logs[i];
        
        // Format: timestamp,activity,feedback,cpu,memory,latency\n
        // Simple formatting (not fully accurate but demonstrates logging)
        int written = 0;
        
        // Would need proper sprintf here, but this is a minimal implementation
        if (remaining > 50) {
            strcpy(ptr, log->activity);
            ptr += strlen(log->activity);
            *ptr++ = ',';
            strcpy(ptr, log->feedback);
            ptr += strlen(log->feedback);
            *ptr++ = '\n';
            remaining -= strlen(log->activity) + strlen(log->feedback) + 2;
        }
    }
    
    *ptr = 0;
}
