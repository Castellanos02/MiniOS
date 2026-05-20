#\!/usr/bin/env python3
import pandas as pd
import numpy as np
import random
import argparse

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
EVENT_POOL = {
    'school':  ['lecture','exam','study_session','assignment_due'],
    'work':    ['team_meeting','presentation','focus_work','deadline'],
    'social':  ['dinner','date','family_time','friends_hangout'],
    'health':  ['gym','doctor_appointment','medication_reminder','therapy'],
    'none':    ['none'],
}
WEATHERS    = ['clear','rain','snow','fog']
MEDIA_TYPES = ['none','music','podcast']

def time_of_day(h):
    if 5  <= h < 12: return 'morning'
    if 12 <= h < 17: return 'afternoon'
    if 17 <= h < 21: return 'evening'
    return 'night'

def assign_label(hour, cat, event, time_until, battery, energy,
                 meal_hrs, brk_mins, tasks, loc, is_wknd, focus,
                 fuel, has_email, msgs_pending, last_media):

    # --- critical needs ---
    if battery < 15:
        return 'charge_phone'
    if (hour >= 23 or hour < 5) and energy < 45:
        return 'sleep_suggestion'
    if meal_hrs > 6:
        return 'eat_something'
    if fuel < 20 and loc == 'commuting':
        return 'find_gas_station'

    # --- arriving at destination ---
    if loc == 'commuting' and 0 <= time_until < 10:
        return 'find_parking'

    # --- running late ---
    if time_until < -10 and cat in ('work','school','social') and msgs_pending > 0:
        return 'send_late_message'

    # --- proactive email alert ---
    if has_email == 1 and cat == 'none' and 8 <= hour < 20:
        return 'read_email_alert'

    # --- commute media suggestions ---
    if loc == 'commuting' and energy < 45 and last_media == 'music':
        return 'play_music'
    if loc == 'commuting' and time_of_day(hour) == 'morning' and last_media == 'podcast':
        return 'play_podcast'
    if loc == 'commuting' and time_of_day(hour) == 'morning':
        return 'play_music'

    # --- proactive repeat suggestion ---
    if loc == 'commuting' and last_media in ('music','podcast') and 6 <= hour < 22:
        return 'suggest_repeat_action'

    # --- upcoming event actions ---
    if cat != 'none' and 20 <= time_until <= 40 and loc in ('home','outside'):
        return 'start_commute'
    if time_until < 5 and cat in ('school','work') and event in (
            'lecture','exam','team_meeting','presentation'):
        return 'silence_phone'
    if 5 <= time_until < 30 and cat == 'work' and event in ('team_meeting','presentation'):
        return 'prepare_for_meeting'
    if 30 <= time_until <= 120 and cat == 'school' and event in ('lecture','exam','study_session'):
        return 'study_for_class'
    if brk_mins > 90 and cat in ('school','work'):
        return 'take_break'
    if cat == 'health' and event == 'medication_reminder' and time_until < 15:
        return 'take_medication'
    if cat == 'social' and 5 <= time_until < 30:
        return 'get_ready'

    # --- free time ---
    if cat == 'none':
        if tasks >= 4 and energy > 60 and 8 <= hour < 20:
            return 'focus_session'
        if energy > 65 and 6 <= hour < 20:
            return 'exercise_suggestion'
        if is_wknd and 13 <= hour <= 20:
            return 'social_suggestion'
        if 6 <= hour < 9 and tasks < 3:
            return 'plan_day'
        if hour >= 20:
            return 'wind_down'

    return 'no_action'

def generate(n, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    rows = []
    for _ in range(n):
        hour = int(np.random.randint(0, 24))
        dow = int(np.random.randint(0, 7))
        is_wknd = int(dow >= 5)
        if hour < 6 or hour >= 22:
            cat_w = [0.05, 0.05, 0.10, 0.05, 0.75]
        elif is_wknd:
            cat_w = [0.05, 0.05, 0.35, 0.20, 0.35]
        else:
            cat_w = [0.25, 0.30, 0.15, 0.15, 0.15]
        cat = str(np.random.choice(['school','work','social','health','none'], p=cat_w))
        event = str(random.choice(EVENT_POOL[cat]))
        time_until = int(np.random.randint(-30, 180)) if cat != 'none' else 999
        battery = float(round(np.clip(np.random.normal(72, 25), 5, 100), 1))
        energy = float(round(np.random.uniform(10, 100), 1))
        meal_hrs = float(round(np.clip(np.random.exponential(2.0), 0, 10), 2))
        brk_mins = float(round(np.random.uniform(0, 180), 1))
        tasks = int(np.random.randint(0, 11))
        weather = str(np.random.choice(WEATHERS, p=[0.55, 0.25, 0.10, 0.10]))
        focus = float(round(np.random.uniform(0, 100), 1))
        fuel = float(round(np.clip(np.random.normal(65, 25), 5, 100), 1))
        has_email = int(np.random.choice([0, 1], p=[0.75, 0.25]))
        msgs_pend = int(np.random.randint(0, 6))
        last_media = str(np.random.choice(MEDIA_TYPES, p=[0.40, 0.35, 0.25]))

        if cat == 'school': loc = 'school'
        elif cat == 'work': loc = 'work'
        elif cat == 'health' and event == 'gym': loc = 'gym'
        elif cat == 'social' and event == 'dinner': loc = 'restaurant'
        elif cat != 'none' and time_until < 20: loc = 'commuting'
        else:                             loc = str(random.choice(['home','home','outside']))

        # extra commuting rows so media/gas/parking labels appear
        if cat in ('work','school') and 5 <= hour <= 9 and time_until < 60:
            loc = 'commuting'

        label = assign_label(hour, cat, event, time_until, battery, energy,
                             meal_hrs, brk_mins, tasks, loc, is_wknd, focus,
                             fuel, has_email, msgs_pend, last_media)
        rows.append({
            'hour': hour,
            'time_of_day': time_of_day(hour),
            'day_of_week': dow, 'is_weekend': is_wknd,
            'event_category': cat, 'scheduled_event': event,
            'time_until_event_min': time_until, 'location': loc,
            'energy_level': energy, 'phone_battery_pct': battery,
            'tasks_pending': tasks, 'last_meal_hours_ago': meal_hrs,
            'last_break_minutes_ago': brk_mins, 'weather': weather,
            'focus_score': focus,
            'fuel_level_pct': fuel,
            'has_unread_email': has_email,
            'messages_pending': msgs_pend,
            'last_media': last_media,
            'is_night': int(hour >= 21 or hour < 6),
            'suggestion_name': label,
        })
    df = pd.DataFrame(rows)
    labels = sorted(df['suggestion_name'].unique())
    df['suggestion_label'] = df['suggestion_name'].map({l: i for i, l in enumerate(labels)})
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows',   type=int, default=1000)
    parser.add_argument('--seed',   type=int, default=42)
    parser.add_argument('--output', default='general_assistant_dataset.csv')
    args = parser.parse_args()
    print("Generating " + str(args.rows) + " rows...")
    df = generate(args.rows, seed=args.seed)
    print("Shape:", df.shape)
    print("\nLabel distribution:\n", df['suggestion_name'].value_counts().to_string())
    print("\nEvent categories:\n", df['event_category'].value_counts().to_string())
    df.to_csv(args.output, index=False)
    print("\nSaved to:", args.output)

if __name__ == '__main__':
    main()