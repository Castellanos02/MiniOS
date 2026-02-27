// proactive_ml.c - Proactive machine learning engine
// Monitors context, predicts needs, suggests activities before user asks

#include <stdint.h>
#include <stddef.h>

// ============================================================================
// CONTEXT MONITORING SYSTEM
// ============================================================================

// Time-based context (simulated - no RTC yet)
typedef struct {
    uint32_t cycles_since_boot;      // CPU cycles as time proxy
    uint8_t estimated_hour;           // 0-23 (derived from cycles)
    uint8_t time_segment;             // 0=morning, 1=afternoon, 2=evening, 3=night
    uint32_t idle_cycles;             // Cycles with no activity
    uint32_t active_cycles;           // Cycles with user interaction
} TimeContext;

// User behavior pattern
typedef struct {
    uint8_t recent_accepts;           // Accepts in last 10 suggestions
    uint8_t recent_rejects;           // Rejects in last 10 suggestions
    uint8_t activity_preference[20];  // Frequency of each activity accepted
    uint32_t average_response_time;   // Cycles between suggest and respond
    uint8_t engagement_level;         // 0-100 (how engaged user is)
} BehaviorPattern;

// System state context
typedef struct {
    uint32_t total_suggestions_made;
    uint32_t total_accepts;
    uint32_t total_rejects;
    uint32_t consecutive_idles;       // Suggestions ignored in a row
    uint8_t current_activity_type;    // Last accepted activity type
    uint8_t energy_level;             // 0-100 (based on activity patterns)
} SystemState;

// Combined context
typedef struct {
    TimeContext time;
    BehaviorPattern behavior;
    SystemState state;
    uint8_t context_confidence;       // How confident we are in context (0-100)
} Context;

static Context g_context = {0};

// Activity categories with time/energy preferences
typedef enum {
    ACT_PHYSICAL = 0,    // Physical activities (morning/high energy)
    ACT_MENTAL,          // Mental activities (morning/afternoon)
    ACT_SOCIAL,          // Social activities (afternoon/evening)
    ACT_PRODUCTIVE,      // Productive tasks (morning/afternoon)
    ACT_CREATIVE,        // Creative work (varied)
    ACT_WELLNESS,        // Wellness/rest (evening/night)
    ACT_LEARNING,        // Learning activities (morning/afternoon)
    ACT_LEISURE          // Leisure/fun (evening/night)
} ActivityCategory;

// Enhanced activity with metadata
typedef struct {
    const char* description;
    ActivityCategory category;
    uint8_t energy_requirement;    // 0-100 (how much energy needed)
    uint8_t time_preference;       // 0=morning, 1=afternoon, 2=evening, 3=any
    uint8_t duration_minutes;      // Typical duration
    float success_rate;            // Historical success rate (0.0-1.0)
} Activity;

// Expanded activity database
static Activity g_activities[] = {
    // Physical (morning/high energy)
    {"Take a 15-minute walk outside", ACT_PHYSICAL, 60, 0, 15, 0.8f},
    {"Do 10 minutes of stretching", ACT_PHYSICAL, 40, 0, 10, 0.9f},
    {"Quick 5-minute workout", ACT_PHYSICAL, 80, 0, 5, 0.7f},
    
    // Mental (morning/afternoon)
    {"Review your weekly goals", ACT_MENTAL, 50, 0, 15, 0.75f},
    {"Plan tomorrow's tasks", ACT_MENTAL, 40, 1, 10, 0.85f},
    {"Practice a new skill for 10 minutes", ACT_LEARNING, 60, 1, 10, 0.7f},
    
    // Social (afternoon/evening)
    {"Call a friend or family member", ACT_SOCIAL, 50, 2, 20, 0.6f},
    {"Send a thoughtful message to someone", ACT_SOCIAL, 30, 3, 5, 0.8f},
    {"Schedule coffee with a colleague", ACT_SOCIAL, 40, 1, 5, 0.65f},
    
    // Productive (morning/afternoon)
    {"Organize your workspace", ACT_PRODUCTIVE, 50, 0, 15, 0.85f},
    {"Clear your email inbox", ACT_PRODUCTIVE, 45, 1, 20, 0.7f},
    {"Update your to-do list", ACT_PRODUCTIVE, 35, 3, 10, 0.9f},
    
    // Creative (varied)
    {"Work on a creative project", ACT_CREATIVE, 70, 3, 30, 0.75f},
    {"Journal for 10 minutes", ACT_CREATIVE, 30, 2, 10, 0.8f},
    {"Brainstorm new ideas", ACT_CREATIVE, 60, 1, 15, 0.7f},
    
    // Wellness (evening/night)
    {"Practice mindfulness meditation", ACT_WELLNESS, 20, 2, 15, 0.85f},
    {"Take a few deep breaths", ACT_WELLNESS, 10, 3, 3, 0.95f},
    {"Read a chapter from your book", ACT_WELLNESS, 25, 2, 20, 0.8f},
    
    // Learning
    {"Watch an educational video", ACT_LEARNING, 35, 1, 15, 0.75f},
    {"Read an article about something new", ACT_LEARNING, 40, 1, 10, 0.8f},
    
    // Leisure
    {"Listen to your favorite music", ACT_LEISURE, 15, 3, 10, 0.9f}
};

#define NUM_ACTIVITIES (sizeof(g_activities) / sizeof(Activity))

// ============================================================================
// CONTEXT ANALYSIS ENGINE
// ============================================================================

// Update time context based on CPU cycles
static void update_time_context(uint32_t cycle_delta) {
    g_context.time.cycles_since_boot += cycle_delta;
    
    // Estimate hour (crude: assume 1M cycles ≈ 1 minute on modern CPU)
    // This is highly approximate but gives us a time sense
    uint32_t estimated_minutes = g_context.time.cycles_since_boot / 1000000;
    g_context.time.estimated_hour = (estimated_minutes / 60) % 24;
    
    // Determine time segment
    if (g_context.time.estimated_hour >= 6 && g_context.time.estimated_hour < 12) {
        g_context.time.time_segment = 0; // Morning
    } else if (g_context.time.estimated_hour >= 12 && g_context.time.estimated_hour < 17) {
        g_context.time.time_segment = 1; // Afternoon
    } else if (g_context.time.estimated_hour >= 17 && g_context.time.estimated_hour < 22) {
        g_context.time.time_segment = 2; // Evening
    } else {
        g_context.time.time_segment = 3; // Night
    }
}

// Calculate user engagement level
static void update_engagement_level(void) {
    // Base engagement on accept/reject ratio and response time
    uint32_t total = g_context.state.total_accepts + g_context.state.total_rejects;
    
    if (total == 0) {
        g_context.behavior.engagement_level = 50; // Neutral
        return;
    }
    
    // Calculate engagement (0-100)
    float accept_ratio = (float)g_context.state.total_accepts / total;
    float idle_penalty = (float)g_context.state.consecutive_idles * 10.0f;
    
    g_context.behavior.engagement_level = (uint8_t)(accept_ratio * 100.0f - idle_penalty);
    
    // Clamp to 0-100
    if (g_context.behavior.engagement_level > 100) {
        g_context.behavior.engagement_level = 100;
    }
}

// Estimate energy level based on activity patterns
static void update_energy_level(void) {
    // Morning: high energy
    // Afternoon: medium-high
    // Evening: medium
    // Night: low
    
    uint8_t base_energy = 0;
    switch (g_context.time.time_segment) {
        case 0: base_energy = 80; break; // Morning
        case 1: base_energy = 70; break; // Afternoon
        case 2: base_energy = 50; break; // Evening
        case 3: base_energy = 30; break; // Night
    }
    
    // Adjust based on recent activity accepts
    // Accepting high-energy activities → user has energy
    // Accepting low-energy activities → user is tired
    
    g_context.state.energy_level = base_energy;
}

// Calculate context confidence
static void update_context_confidence(void) {
    // More data → higher confidence
    uint32_t total_interactions = g_context.state.total_accepts + g_context.state.total_rejects;
    
    if (total_interactions < 5) {
        g_context.context_confidence = 30;
    } else if (total_interactions < 20) {
        g_context.context_confidence = 60;
    } else {
        g_context.context_confidence = 90;
    }
}

// Main context update (called periodically)
void update_context(uint32_t cycle_delta, uint8_t user_idle) {
    update_time_context(cycle_delta);
    
    if (user_idle) {
        g_context.time.idle_cycles += cycle_delta;
        g_context.state.consecutive_idles++;
    } else {
        g_context.time.active_cycles += cycle_delta;
        g_context.state.consecutive_idles = 0;
    }
    
    update_engagement_level();
    update_energy_level();
    update_context_confidence();
}

// ============================================================================
// PROACTIVE SUGGESTION ENGINE
// ============================================================================

// Score an activity based on current context
static float score_activity(uint8_t activity_idx) {
    Activity* act = &g_activities[activity_idx];
    float score = 0.0f;
    
    // 1. Time preference match (0-30 points)
    if (act->time_preference == 3) {
        // Any time is fine
        score += 20.0f;
    } else if (act->time_preference == g_context.time.time_segment) {
        // Perfect time match
        score += 30.0f;
    } else {
        // Wrong time - penalty
        score += 5.0f;
    }
    
    // 2. Energy level match (0-30 points)
    int energy_diff = (int)act->energy_requirement - (int)g_context.state.energy_level;
    if (energy_diff < 0) energy_diff = -energy_diff;
    
    if (energy_diff < 15) {
        score += 30.0f; // Good energy match
    } else if (energy_diff < 30) {
        score += 20.0f; // Acceptable
    } else {
        score += 5.0f;  // Poor match
    }
    
    // 3. Historical success rate (0-20 points)
    score += act->success_rate * 20.0f;
    
    // 4. User preference for this activity (0-20 points)
    if (activity_idx < 20) {
        score += g_context.behavior.activity_preference[activity_idx] * 2.0f;
    }
    
    // 5. Avoid recent activities (diversity bonus)
    if (activity_idx != g_context.state.current_activity_type) {
        score += 10.0f;
    }
    
    return score;
}

// Select best activity proactively
uint8_t proactive_suggest_activity(void) {
    float best_score = 0.0f;
    uint8_t best_idx = 0;
    
    // Score all activities
    for (uint8_t i = 0; i < NUM_ACTIVITIES; i++) {
        float score = score_activity(i);
        
        if (score > best_score) {
            best_score = score;
            best_idx = i;
        }
    }
    
    g_context.state.total_suggestions_made++;
    return best_idx;
}

// Update context based on user response
void record_user_response(uint8_t activity_idx, uint8_t accepted) {
    if (accepted) {
        g_context.state.total_accepts++;
        g_context.state.current_activity_type = activity_idx;
        
        // Increase preference for this activity
        if (activity_idx < 20) {
            if (g_context.behavior.activity_preference[activity_idx] < 10) {
                g_context.behavior.activity_preference[activity_idx]++;
            }
        }
        
        // Update activity success rate
        if (activity_idx < NUM_ACTIVITIES) {
            g_activities[activity_idx].success_rate = 
                (g_activities[activity_idx].success_rate * 0.9f) + 0.1f;
        }
        
    } else {
        g_context.state.total_rejects++;
        
        // Decrease preference for this activity
        if (activity_idx < 20) {
            if (g_context.behavior.activity_preference[activity_idx] > 0) {
                g_context.behavior.activity_preference[activity_idx]--;
            }
        }
        
        // Update activity success rate
        if (activity_idx < NUM_ACTIVITIES) {
            g_activities[activity_idx].success_rate = 
                (g_activities[activity_idx].success_rate * 0.9f);
        }
    }
    
    g_context.state.consecutive_idles = 0;
}

// Check if we should proactively suggest (don't spam user!)
uint8_t should_suggest_now(void) {
    // Don't suggest if:
    // 1. User just saw a suggestion (wait for response or timeout)
    // 2. User engagement is very low
    // 3. Too many consecutive ignored suggestions
    
    if (g_context.state.consecutive_idles > 3) {
        return 0; // User is ignoring us
    }
    
    if (g_context.behavior.engagement_level < 20) {
        return 0; // User doesn't want suggestions
    }
    
    // Suggest based on idle time
    // After ~30 seconds of idle (30M cycles), suggest proactively
    if (g_context.time.idle_cycles > 30000000) {
        return 1;
    }
    
    return 0;
}

// Get activity description
const char* get_activity_description(uint8_t idx) {
    if (idx < NUM_ACTIVITIES) {
        return g_activities[idx].description;
    }
    return "Unknown activity";
}

// Get context summary for display
void get_context_summary(char* buffer, size_t size) {
    const char* time_names[] = {"Morning", "Afternoon", "Evening", "Night"};
    const char* time = time_names[g_context.time.time_segment];
    
    // Simple string formatting (no snprintf in kernel)
    buffer[0] = '\0'; // Start with empty string
    
    // Just return basic info for now
    // In full implementation, build string with time, energy, engagement
}
