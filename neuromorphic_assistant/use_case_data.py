#!/usr/bin/env python3
"""
Use Case Training Data Generator
Based on real MiniOS use cases from requirements document

Implements:
- Default preferences (music, routes, activities)
- Proactive suggestions (fills idle time)
- Learning from accept/reject feedback
- Context-aware recommendations
"""

import numpy as np
import torch


# ============================================================
# Use Case Categories
# ============================================================

USE_CASES = {
    # Navigation & Travel
    'suggest_route_to_work': {
        'default': 'highway_route',
        'alternatives': ['scenic_route', 'shortest_route', 'avoid_tolls'],
        'context': 'driving to work, morning hours',
    },
    'suggest_gas_station': {
        'default': 'cheapest',
        'alternatives': ['closest', 'premium_gas', 'familiar_brand'],
        'context': 'low fuel, on route',
    },
    'suggest_parking': {
        'default': 'usual_entrance',
        'alternatives': ['closest_spot', 'covered_parking', 'free_parking'],
        'context': 'arriving at destination',
    },
    
    # Music & Entertainment
    'suggest_music': {
        'default': '90s_road_trip',
        'alternatives': ['daily_drive', 'smooth_jazz', 'top_100', 'random_radio'],
        'context': 'driving, no specific request',
    },
    'suggest_podcast': {
        'default': 'continue_last',
        'alternatives': ['new_episode', 'different_podcast', 'audiobook'],
        'context': 'long drive, commute',
    },
    
    # Proactive Time-Filling Suggestions
    'suggest_morning_activity': {
        'default': 'workout',
        'alternatives': ['quick_breakfast', 'review_schedule', 'news_briefing'],
        'context': 'morning, before work, 30min free',
    },
    'suggest_lunch_break': {
        'default': 'quick_walk',
        'alternatives': ['grab_lunch', 'power_nap', 'catch_up_emails'],
        'context': 'midday, 1 hour free',
    },
    'suggest_afternoon_break': {
        'default': 'stretch_break',
        'alternatives': ['coffee_run', 'social_chat', 'quick_task'],
        'context': 'afternoon, 15min free',
    },
    'suggest_evening_activity': {
        'default': 'relax',
        'alternatives': ['exercise', 'hobby_time', 'social_plans'],
        'context': 'after work, 2 hours free',
    },
    'suggest_weekend_morning': {
        'default': 'sleep_in',
        'alternatives': ['early_workout', 'breakfast_out', 'productive_tasks'],
        'context': 'weekend morning, no plans',
    },
    
    # Communication
    'suggest_text_buddy': {
        'default': 'running_late',
        'alternatives': ['on_my_way', 'custom_message'],
        'context': 'late for meeting with friend',
    },
    'suggest_email_action': {
        'default': 'read_aloud',
        'alternatives': ['skip_for_now', 'quick_reply', 'archive'],
        'context': 'email from manager while driving',
    },
    
    # Contextual Idle Time Filling
    'suggest_short_idle_5min': {
        'default': 'quick_breathing',
        'alternatives': ['check_messages', 'quick_stretch', 'just_relax'],
        'context': '5 minutes idle, any time',
    },
    'suggest_medium_idle_20min': {
        'default': 'light_task',
        'alternatives': ['short_walk', 'snack_break', 'organize_notes'],
        'context': '20 minutes idle',
    },
    'suggest_long_idle_1hour': {
        'default': 'deep_work',
        'alternatives': ['learn_something', 'creative_project', 'social_activity'],
        'context': '1+ hour idle',
    },
}


# ============================================================
# User Profile with Preferences
# ============================================================

class UserProfile:
    """Stores user preferences that evolve based on feedback"""
    
    def __init__(self):
        # Default preferences (before learning)
        self.preferences = {
            'music_genre': '90s_road_trip',
            'route_preference': 'highway',
            'gas_preference': 'cheapest',
            'morning_routine': 'workout',
            'break_activity': 'quick_walk',
            'evening_activity': 'relax',
            'podcast_continue': True,
            'parking_spot': 'usual_entrance',
        }
        
        # Acceptance/rejection history
        self.history = {
            'accepts': {},
            'rejects': {},
        }
        
        # Time preferences (learned from accepts/rejects)
        self.time_preferences = {
            'morning_energy': 70,    # Prefers active morning
            'evening_energy': 40,    # Prefers relaxed evening
            'workout_time': 7,       # 7 AM
            'deep_work_time': 9,     # 9 AM
            'break_frequency': 90,   # Minutes between breaks
        }
    
    def update_preference(self, category, choice, accepted):
        """Update preferences based on user feedback"""
        
        if accepted:
            self.preferences[category] = choice
            self.history['accepts'][category] = self.history['accepts'].get(category, 0) + 1
        else:
            self.history['rejects'][category] = self.history['rejects'].get(category, 0) + 1
    
    def get_preference(self, category):
        """Get current preference for a category"""
        return self.preferences.get(category, 'default')


# ============================================================
# Context-Aware Training Data Generator
# ============================================================

def generate_use_case_training_data(num_samples=500):
    """
    Generate training data based on use cases
    
    Returns realistic scenarios with:
    - Time context
    - User state (energy, engagement)
    - Calendar gaps (idle time)
    - Default preferences
    - Learning opportunities
    """
    
    X_list = []
    y_list = []
    scenarios = []
    
    # Create diverse scenarios
    for i in range(num_samples):
        # Random time and state
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        day_of_week = np.random.randint(0, 7)  # 0=Mon, 6=Sun
        
        # User state
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        
        # Calendar context
        has_meeting = np.random.random() < 0.3  # 30% chance of meeting
        idle_duration = 0 if has_meeting else np.random.choice([5, 15, 30, 60, 120, 180])
        
        # Recent feedback (simulated learning)
        recent_accepts = np.random.randint(0, 10)
        recent_rejects = np.random.randint(0, 10)
        
        # Feature vector
        features = [
            hour / 24.0,                          # 0: Normalized hour
            minute / 60.0,                        # 1: Normalized minute
            day_of_week / 7.0,                    # 2: Day of week
            energy / 100.0,                       # 3: Energy level
            engagement / 100.0,                   # 4: Engagement
            idle_duration / 180.0,                # 5: Idle time (normalized to 3 hours)
            1.0 if has_meeting else 0.0,          # 6: Has upcoming meeting
            recent_accepts / 10.0,                # 7: Recent accepts
            recent_rejects / 10.0,                # 8: Recent rejects
            1.0 if day_of_week >= 5 else 0.0,     # 9: Is weekend
        ]
        
        # Determine suggestion based on context
        suggestion = determine_proactive_suggestion(
            hour, day_of_week, energy, engagement, 
            idle_duration, has_meeting
        )
        
        X_list.append(features)
        y_list.append(suggestion['label'])
        scenarios.append({
            'hour': hour,
            'minute': minute,
            'day': day_of_week,
            'energy': energy,
            'idle_minutes': idle_duration,
            'suggestion': suggestion['name'],
            'reason': suggestion['reason'],
        })
    
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int64)
    
    return X, y, scenarios


def determine_proactive_suggestion(hour, day_of_week, energy, engagement, 
                                   idle_duration, has_meeting):
    """
    Determine proactive suggestion based on context
    
    This implements the core intelligence:
    - Fills idle time proactively
    - Considers time of day
    - Adapts to user state
    - Provides contextual defaults
    """
    
    is_weekend = day_of_week >= 5
    is_morning = 6 <= hour < 12
    is_afternoon = 12 <= hour < 17
    is_evening = 17 <= hour < 22
    is_night = hour >= 22 or hour < 6
    
    # PROACTIVE: Fill idle time with suggestions
    if idle_duration > 0:
        
        # Short idle (5-15 min)
        if idle_duration <= 15:
            if energy < 40:
                return {'label': 0, 'name': 'quick_rest', 'reason': 'Low energy, short break'}
            elif engagement < 30:
                return {'label': 1, 'name': 'stretch_break', 'reason': 'Low engagement, move around'}
            else:
                return {'label': 2, 'name': 'quick_task', 'reason': 'Good state, productive'}
        
        # Medium idle (15-60 min)
        elif idle_duration <= 60:
            if is_morning and energy > 60:
                return {'label': 3, 'name': 'workout', 'reason': 'Morning + energy = exercise'}
            elif hour == 12 or hour == 13:
                return {'label': 4, 'name': 'lunch_break', 'reason': 'Lunchtime'}
            elif engagement > 60:
                return {'label': 5, 'name': 'creative_work', 'reason': 'High engagement'}
            else:
                return {'label': 6, 'name': 'light_activity', 'reason': 'Medium idle time'}
        
        # Long idle (1+ hours)
        else:
            if is_morning and not is_weekend and engagement > 50:
                return {'label': 7, 'name': 'deep_work', 'reason': 'Morning focus time'}
            elif is_afternoon and energy > 60:
                return {'label': 8, 'name': 'productive_project', 'reason': 'Afternoon productivity'}
            elif is_evening and energy < 50:
                return {'label': 9, 'name': 'relax', 'reason': 'Evening wind-down'}
            elif is_weekend and is_morning:
                return {'label': 10, 'name': 'hobby_time', 'reason': 'Weekend leisure'}
            else:
                return {'label': 11, 'name': 'flexible_activity', 'reason': 'Free time'}
    
    # Has meeting/activity planned
    else:
        if is_morning:
            return {'label': 12, 'name': 'prepare_for_meeting', 'reason': 'Upcoming meeting'}
        elif is_afternoon:
            return {'label': 13, 'name': 'review_notes', 'reason': 'Meeting prep'}
        else:
            return {'label': 14, 'name': 'stay_ready', 'reason': 'Active schedule'}
    
    # Default fallback
    return {'label': 15, 'name': 'check_in', 'reason': 'General suggestion'}


# ============================================================
# Activity Labels (Expanded for Use Cases)
# ============================================================

ACTIVITY_LABELS = [
    # Idle time filling (0-11)
    "quick_rest",           # 0: 5min idle, low energy
    "stretch_break",        # 1: 5min idle, low engagement
    "quick_task",           # 2: 5min idle, productive
    "workout",              # 3: 30min idle, morning, high energy
    "lunch_break",          # 4: 30min idle, midday
    "creative_work",        # 5: 30min idle, high engagement
    "light_activity",       # 6: 30min idle, general
    "deep_work",            # 7: 1hr+ idle, morning focus
    "productive_project",   # 8: 1hr+ idle, afternoon
    "relax",                # 9: 1hr+ idle, evening
    "hobby_time",           # 10: 1hr+ idle, weekend
    "flexible_activity",    # 11: 1hr+ idle, free time
    
    # Meeting context (12-14)
    "prepare_for_meeting",  # 12: Before meeting
    "review_notes",         # 13: Meeting prep
    "stay_ready",           # 14: Active schedule
    
    # General (15-19)
    "check_in",             # 15: Default
    "music_suggestion",     # 16: Driving/idle
    "podcast_suggestion",   # 17: Long commute
    "route_suggestion",     # 18: Navigation
    "social_suggestion",    # 19: Evening/weekend
]


# ============================================================
# Test Function
# ============================================================

if __name__ == "__main__":
    print("="*70)
    print("USE CASE TRAINING DATA GENERATOR")
    print("="*70)
    
    # Generate data
    print("\nGenerating 500 training samples...")
    X, y, scenarios = generate_use_case_training_data(500)
    
    print(f"\n✓ Generated {len(X)} samples")
    print(f"  Feature dimensions: {X.shape[1]}")
    print(f"  Number of activities: {len(ACTIVITY_LABELS)}")
    
    # Show sample scenarios
    print("\n" + "="*70)
    print("SAMPLE SCENARIOS (Proactive Suggestions)")
    print("="*70)
    
    for i in range(10):
        s = scenarios[i]
        day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][s['day']]
        
        print(f"\nScenario {i+1}:")
        print(f"  Time: {day_name} {s['hour']:02d}:{s['minute']:02d}")
        print(f"  Energy: {s['energy']}/100")
        print(f"  Idle time: {s['idle_minutes']} minutes")
        print(f"  → Suggestion: {s['suggestion']}")
        print(f"  → Reason: {s['reason']}")
    
    print("\n" + "="*70)
    print("✓ Use case data ready for training!")
    print("="*70)
