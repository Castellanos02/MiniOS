// proactive_suggestions.c - Proactive suggestion engine
// Monitors calendar and suggests actions before/during events

#include <stdint.h>

// =============================================================================
// PROACTIVE SUGGESTION TYPES
// =============================================================================

typedef enum {
    SUGGEST_PREPARE,      // Before event (5-15 min before)
    SUGGEST_DURING,       // During event
    SUGGEST_TRANSITION,   // Between events (wrap-up/prepare)
    SUGGEST_IDLE          // No events nearby
} SuggestionTiming;

typedef enum {
    ACTION_SILENCE_PHONE,
    ACTION_SET_REMINDER,
    ACTION_OPEN_NOTES,
    ACTION_START_TIMER,
    ACTION_PLAY_MUSIC,
    ACTION_PLAY_VIDEO,
    ACTION_STRETCH,
    ACTION_HYDRATE,
    ACTION_PREPARE_MATERIALS,
    ACTION_REVIEW_AGENDA,
    ACTION_CLOSE_DISTRACTIONS,
    ACTION_TAKE_BREAK,
    ACTION_SAVE_WORK,
    ACTION_SEND_UPDATE,
    ACTION_BREATHE
} ActionType;

typedef struct {
    ActionType action;
    const char* description;
    uint8_t priority;         // 0-100 (higher = more important)
    uint8_t duration_seconds; // How long to show
    uint8_t auto_execute;     // 1 = can auto-execute, 0 = ask first
} ProactiveSuggestion;

// =============================================================================
// EVENT-ACTION MAPPING
// =============================================================================

// Suggestions for "Team Meeting"
static ProactiveSuggestion meeting_prepare[] = {
    {ACTION_SILENCE_PHONE, "Silence phone for meeting", 90, 10, 1},
    {ACTION_REVIEW_AGENDA, "Review meeting agenda", 80, 15, 0},
    {ACTION_OPEN_NOTES, "Open note-taking app", 70, 10, 1},
    {ACTION_CLOSE_DISTRACTIONS, "Close social media tabs", 85, 10, 1}
};

static ProactiveSuggestion meeting_during[] = {
    {ACTION_TAKE_BREAK, "Take notes on key points", 60, 0, 0},
    {ACTION_HYDRATE, "Stay hydrated - drink water", 40, 5, 0}
};

// Suggestions for "Lunch Break"
static ProactiveSuggestion lunch_prepare[] = {
    {ACTION_SAVE_WORK, "Save your work before break", 95, 10, 1},
    {ACTION_SET_REMINDER, "Set reminder to return", 60, 10, 0}
};

static ProactiveSuggestion lunch_during[] = {
    {ACTION_PLAY_MUSIC, "Play relaxing playlist", 70, 10, 0},
    {ACTION_PLAY_VIDEO, "Watch: 'Chef's Table' episode", 60, 10, 0},
    {ACTION_STRETCH, "Do light stretches while eating", 50, 10, 0}
};

// Suggestions for "Project Work"
static ProactiveSuggestion work_prepare[] = {
    {ACTION_CLOSE_DISTRACTIONS, "Close unnecessary apps", 85, 10, 1},
    {ACTION_PREPARE_MATERIALS, "Gather project files", 75, 10, 0},
    {ACTION_START_TIMER, "Start focus timer (45 min)", 80, 10, 0}
};

static ProactiveSuggestion work_during[] = {
    {ACTION_TAKE_BREAK, "Mini break: 2-minute stretch", 50, 5, 0},
    {ACTION_HYDRATE, "Drink water", 40, 5, 0}
};

// Suggestions for "Coffee Break"
static ProactiveSuggestion break_prepare[] = {
    {ACTION_SAVE_WORK, "Save current work", 90, 10, 1}
};

static ProactiveSuggestion break_during[] = {
    {ACTION_STRETCH, "Stretch your legs", 70, 10, 0},
    {ACTION_PLAY_MUSIC, "Play energizing music", 60, 10, 0},
    {ACTION_BREATHE, "Take 3 deep breaths", 50, 5, 0}
};

// Generic suggestions for AI-suggested activities
static ProactiveSuggestion ai_activity_prepare[] = {
    {ACTION_SET_REMINDER, "Set reminder for activity", 60, 10, 0},
    {ACTION_PREPARE_MATERIALS, "Prepare what you need", 70, 10, 0}
};

// =============================================================================
// PROACTIVE ENGINE STATE
// =============================================================================

typedef struct {
    uint8_t current_hour;
    uint8_t current_minute;
    uint8_t last_suggestion_event;   // Which event we last suggested for
    uint8_t last_suggestion_type;    // PREPARE/DURING/etc
    uint32_t last_suggestion_time;   // Cycle count when suggested
    uint8_t suggestions_shown[20];   // Track which suggestions shown per event
    uint8_t auto_executed[20];       // Track which actions auto-executed
} ProactiveState;

static ProactiveState g_proactive = {0};

// =============================================================================
// SUGGESTION SELECTION LOGIC
// =============================================================================

// Get time until event (in minutes, can be negative if past)
static int16_t get_minutes_until_event(uint8_t event_hour, uint8_t event_minute,
                                       uint8_t current_hour, uint8_t current_minute) {
    int16_t event_mins = event_hour * 60 + event_minute;
    int16_t current_mins = current_hour * 60 + current_minute;
    return event_mins - current_mins;
}

// Check if currently during an event
static uint8_t is_during_event(uint8_t event_hour, uint8_t event_minute, 
                               uint8_t duration,
                               uint8_t current_hour, uint8_t current_minute) {
    int16_t mins_until = get_minutes_until_event(event_hour, event_minute,
                                                  current_hour, current_minute);
    return (mins_until <= 0 && mins_until > -duration);
}

// Get suggestions for an event based on title
static void get_event_suggestions(const char* event_title, uint8_t is_ai_suggestion,
                                  SuggestionTiming timing,
                                  ProactiveSuggestion** suggestions,
                                  uint8_t* count) {
    *suggestions = NULL;
    *count = 0;
    
    // Helper function to check if string contains substring
    auto uint8_t contains(const char* str, const char* substr) {
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
    
    // AI suggestions get generic prep
    if (is_ai_suggestion && timing == SUGGEST_PREPARE) {
        *suggestions = ai_activity_prepare;
        *count = sizeof(ai_activity_prepare) / sizeof(ProactiveSuggestion);
        return;
    }
    
    // Match event type
    if (contains(event_title, "Meeting") || contains(event_title, "meeting")) {
        if (timing == SUGGEST_PREPARE) {
            *suggestions = meeting_prepare;
            *count = sizeof(meeting_prepare) / sizeof(ProactiveSuggestion);
        } else if (timing == SUGGEST_DURING) {
            *suggestions = meeting_during;
            *count = sizeof(meeting_during) / sizeof(ProactiveSuggestion);
        }
    }
    else if (contains(event_title, "Lunch") || contains(event_title, "lunch")) {
        if (timing == SUGGEST_PREPARE) {
            *suggestions = lunch_prepare;
            *count = sizeof(lunch_prepare) / sizeof(ProactiveSuggestion);
        } else if (timing == SUGGEST_DURING) {
            *suggestions = lunch_during;
            *count = sizeof(lunch_during) / sizeof(ProactiveSuggestion);
        }
    }
    else if (contains(event_title, "Project") || contains(event_title, "Work")) {
        if (timing == SUGGEST_PREPARE) {
            *suggestions = work_prepare;
            *count = sizeof(work_prepare) / sizeof(ProactiveSuggestion);
        } else if (timing == SUGGEST_DURING) {
            *suggestions = work_during;
            *count = sizeof(work_during) / sizeof(ProactiveSuggestion);
        }
    }
    else if (contains(event_title, "Coffee") || contains(event_title, "Break")) {
        if (timing == SUGGEST_PREPARE) {
            *suggestions = break_prepare;
            *count = sizeof(break_prepare) / sizeof(ProactiveSuggestion);
        } else if (timing == SUGGEST_DURING) {
            *suggestions = break_during;
            *count = sizeof(break_during) / sizeof(ProactiveSuggestion);
        }
    }
}

// =============================================================================
// MAIN PROACTIVE ENGINE
// =============================================================================

typedef struct {
    uint8_t has_suggestion;
    ProactiveSuggestion suggestion;
    SuggestionTiming timing;
    const char* event_title;
    uint8_t event_index;
    uint8_t auto_execute;
} ProactiveResult;

// Main function: Check calendar and return proactive suggestion if any
ProactiveResult check_proactive_suggestions(
    void* events,           // CalendarEvent array
    uint8_t event_count,
    uint8_t current_hour,
    uint8_t current_minute,
    uint32_t current_cycles
) {
    ProactiveResult result = {0};
    g_proactive.current_hour = current_hour;
    g_proactive.current_minute = current_minute;
    
    // Don't spam - wait at least 30 seconds between suggestions
    if (current_cycles - g_proactive.last_suggestion_time < 30000000) {
        return result;
    }
    
    // Check each event
    for (uint8_t i = 0; i < event_count; i++) {
        // Cast to CalendarEvent (we'll define this externally)
        typedef struct {
            uint8_t hour;
            uint8_t minute;
            uint8_t duration;
            const char* title;
            uint8_t is_suggestion;
            uint8_t category;
        } CalendarEvent;
        
        CalendarEvent* evt = &((CalendarEvent*)events)[i];
        
        int16_t mins_until = get_minutes_until_event(evt->hour, evt->minute,
                                                      current_hour, current_minute);
        
        // PREPARE suggestions (10 minutes before)
        if (mins_until > 5 && mins_until <= 10) {
            ProactiveSuggestion* suggestions;
            uint8_t count;
            get_event_suggestions(evt->title, evt->is_suggestion, 
                                SUGGEST_PREPARE, &suggestions, &count);
            
            if (count > 0 && suggestions) {
                // Find highest priority suggestion we haven't shown yet
                for (uint8_t s = 0; s < count; s++) {
                    uint8_t key = i * 10 + s;  // Unique key per event+suggestion
                    if (!g_proactive.suggestions_shown[key % 20]) {
                        result.has_suggestion = 1;
                        result.suggestion = suggestions[s];
                        result.timing = SUGGEST_PREPARE;
                        result.event_title = evt->title;
                        result.event_index = i;
                        result.auto_execute = suggestions[s].auto_execute;
                        
                        g_proactive.suggestions_shown[key % 20] = 1;
                        g_proactive.last_suggestion_time = current_cycles;
                        g_proactive.last_suggestion_event = i;
                        g_proactive.last_suggestion_type = SUGGEST_PREPARE;
                        
                        return result;
                    }
                }
            }
        }
        
        // DURING suggestions (during the event)
        else if (is_during_event(evt->hour, evt->minute, evt->duration,
                                 current_hour, current_minute)) {
            ProactiveSuggestion* suggestions;
            uint8_t count;
            get_event_suggestions(evt->title, evt->is_suggestion,
                                SUGGEST_DURING, &suggestions, &count);
            
            if (count > 0 && suggestions) {
                // Only suggest once during event
                uint8_t key = i * 10 + 5;  // Different key for "during"
                if (!g_proactive.suggestions_shown[key % 20]) {
                    result.has_suggestion = 1;
                    result.suggestion = suggestions[0];  // First suggestion
                    result.timing = SUGGEST_DURING;
                    result.event_title = evt->title;
                    result.event_index = i;
                    result.auto_execute = 0;  // Never auto-execute during
                    
                    g_proactive.suggestions_shown[key % 20] = 1;
                    g_proactive.last_suggestion_time = current_cycles;
                    g_proactive.last_suggestion_event = i;
                    g_proactive.last_suggestion_type = SUGGEST_DURING;
                    
                    return result;
                }
            }
        }
    }
    
    return result;
}

// Execute an action (for auto-executable ones)
void execute_action(ActionType action) {
    // In a real OS, this would actually execute
    // For now, just mark as executed
    // Future: could integrate with phone API, music player, etc.
}

// Reset proactive state (e.g., at midnight)
void reset_proactive_state(void) {
    for (uint8_t i = 0; i < 20; i++) {
        g_proactive.suggestions_shown[i] = 0;
        g_proactive.auto_executed[i] = 0;
    }
}

// =============================================================================
// USER PREFERENCE LEARNING
// =============================================================================

typedef struct {
    ActionType action;
    uint8_t accepted_count;
    uint8_t rejected_count;
    float preference_score;  // 0.0-1.0
} ActionPreference;

static ActionPreference g_action_prefs[15] = {0};  // One per action type

void record_action_feedback(ActionType action, uint8_t accepted) {
    if (action >= 15) return;
    
    if (accepted) {
        g_action_prefs[action].accepted_count++;
    } else {
        g_action_prefs[action].rejected_count++;
    }
    
    // Update preference score
    uint32_t total = g_action_prefs[action].accepted_count + 
                     g_action_prefs[action].rejected_count;
    if (total > 0) {
        g_action_prefs[action].preference_score = 
            (float)g_action_prefs[action].accepted_count / total;
    }
}

// Filter suggestions by user preference
uint8_t should_show_suggestion(ActionType action) {
    if (action >= 15) return 1;
    
    // If user has rejected this action type >70%, don't show
    if (g_action_prefs[action].preference_score < 0.3f &&
        g_action_prefs[action].rejected_count > 3) {
        return 0;
    }
    
    return 1;
}
