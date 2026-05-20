#!/usr/bin/env python3
"""
export_dataset_csv.py
=====================
Generates the 1000-row driving assistant dataset and saves it as a
human-readable CSV file.  Only requires numpy - no torch needed.

Usage:
    python export_dataset_csv.py
    python export_dataset_csv.py --output my_data.csv --samples 1000 --seed 42

Output columns (raw, un-normalised for easy reading):
    hour, minute, time_of_day, day_of_week, is_weekend,
    destination_type, distance_to_dest_miles, gas_level_pct,
    driver_fatigue_level, speed_mph, trip_duration_minutes,
    weather, traffic, heart_rate_bpm, last_break_minutes_ago,
    outside_temp_f, is_night_driving,
    suggestion_label (int), suggestion_name (target)

Plus noisy normalised versions of each continuous feature so you can
see exactly what the SNN receives:
    norm_distance, norm_gas, norm_fatigue, norm_speed, norm_trip,
    norm_heart_rate, norm_last_break, norm_temp
"""

import csv
import argparse
import numpy as np

# ------------------------------------------------------------------ #
#  Inline data-generation logic (no torch dependency)                 #
# ------------------------------------------------------------------ #

DESTINATION_TYPES = [
    'work', 'home', 'gas_station', 'grocery',
    'restaurant', 'hospital', 'gym', 'school',
]
WEATHER_TYPES = ['clear', 'rain', 'snow', 'fog']
TRAFFIC_TYPES = ['low', 'medium', 'high']
TOD_NAMES     = ['night', 'morning', 'afternoon', 'evening']

SUGGESTION_LABELS = [
    'no_action',
    'take_break_now',
    'take_break_soon',
    'refuel_now',
    'refuel_soon',
    'speed_alert',
    'weather_warning',
    'route_to_gas',
    'food_break',
    'arrived_soon',
    'coffee_suggestion',
    'rest_area_ahead',
]

NOISE_STD = 0.03


def _sample_scenario(rng):
    hour        = int(rng.integers(0, 24))
    minute      = int(rng.integers(0, 60))
    day_of_week = int(rng.integers(0, 7))
    is_weekend  = int(day_of_week >= 5)

    if   5  <= hour < 12: tod = 1
    elif 12 <= hour < 17: tod = 2
    elif 17 <= hour < 22: tod = 3
    else:                  tod = 0

    is_night_driving = int(tod == 0 or hour >= 21)

    dest_idx  = int(rng.integers(0, len(DESTINATION_TYPES)))
    dest_type = DESTINATION_TYPES[dest_idx]

    distance = float(np.clip(rng.exponential(scale=12), 0.2, 100))

    gas_low   = rng.random() < 0.20
    gas_level = float(rng.uniform(2, 18) if gas_low else rng.uniform(15, 100))

    base_fatigue = (hour - 6) / 18 * 4 if 6 <= hour <= 24 else 2
    trip_minutes = float(np.clip(rng.exponential(scale=35), 1, 180))
    fatigue = float(np.clip(
        base_fatigue + trip_minutes / 60 * 2 + rng.uniform(-1, 2), 0, 10,
    ))

    speed = float(np.clip(rng.normal(55, 15), 0, 90))

    weather_idx = int(rng.choice([0, 1, 2, 3], p=[0.60, 0.25, 0.08, 0.07]))
    weather     = WEATHER_TYPES[weather_idx]

    traffic_idx = int(rng.choice([0, 1, 2], p=[0.35, 0.40, 0.25]))
    traffic     = TRAFFIC_TYPES[traffic_idx]

    heart_rate = float(np.clip(65 + fatigue * 3 + rng.normal(0, 6), 50, 130))
    last_break = float(np.clip(rng.exponential(scale=45), 0, 180))
    temp_f     = float(rng.uniform(-10, 110))

    return dict(
        hour=hour, minute=minute,
        time_of_day=TOD_NAMES[tod], time_of_day_enc=tod,
        day_of_week=day_of_week,
        day_name=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][day_of_week],
        is_weekend=is_weekend,
        destination_type=dest_type, destination_type_enc=dest_idx,
        distance_to_dest_miles=distance,
        gas_level_pct=gas_level,
        driver_fatigue_level=fatigue,
        speed_mph=speed,
        trip_duration_minutes=trip_minutes,
        weather=weather, weather_enc=weather_idx,
        traffic=traffic, traffic_enc=traffic_idx,
        heart_rate_bpm=heart_rate,
        last_break_minutes_ago=last_break,
        outside_temp_f=temp_f,
        is_night_driving=is_night_driving,
    )


def _label_scenario(s):
    dist = s['distance_to_dest_miles']
    gas = s['gas_level_pct']
    fat = s['driver_fatigue_level']
    spd = s['speed_mph']
    weather = s['weather']
    brk = s['last_break_minutes_ago']
    trip = s['trip_duration_minutes']
    dest = s['destination_type']
    hr = s['heart_rate_bpm']
    tod = s['time_of_day_enc']
    night = s['is_night_driving']

    if fat >= 7.5 or (fat >= 6 and brk > 90) or (night and hr > 105):
        return 1
    if weather in ('snow', 'fog') and spd > 45:
        return 6
    safe_speed = 70 if weather == 'clear' else 55 if weather == 'rain' else 35
    if spd > safe_speed + 10:
        return 5
    if gas <= 10:
        return 3 if dest == 'gas_station' else 7
    if gas <= 25 and dest != 'gas_station':
        return 4
    if dist < 2:
        return 9
    if fat >= 5.5 or (brk > 75 and trip > 60):
        return 1 if night else 2
    if trip > 90 and tod in (1, 2):
        return 8
    if fat >= 3.5 and trip > 45:
        return 10
    if brk > 60 and trip > 70 and spd > 40:
        return 11
    if weather == 'rain' and spd > 60:
        return 6
    return 0


def generate_csv(num_samples=1000, seed=42, noise_std=NOISE_STD, output_path='driving_assistant_dataset.csv'):
    rng = np.random.default_rng(seed)
    rows = []

    for _ in range(num_samples):
        s     = _sample_scenario(rng)
        label = _label_scenario(s)

        # Raw normalised features (before noise)
        norm_dist = s['distance_to_dest_miles']  / 100.0
        norm_gas = s['gas_level_pct']            / 100.0
        norm_fat = s['driver_fatigue_level']     /  10.0
        norm_spd = s['speed_mph']                /  90.0
        norm_trip = s['trip_duration_minutes']    / 180.0
        norm_hr = (s['heart_rate_bpm'] - 50)    /  80.0
        norm_brk = s['last_break_minutes_ago']   / 180.0
        norm_tmp = (s['outside_temp_f'] + 10)    / 120.0

        rows.append(dict(
            # --- Human-readable columns ---
            hour                    = s['hour'],
            minute                  = s['minute'],
            time_of_day             = s['time_of_day'],
            day_name                = s['day_name'],
            day_of_week             = s['day_of_week'],
            is_weekend              = s['is_weekend'],
            destination_type        = s['destination_type'],
            distance_to_dest_miles  = round(s['distance_to_dest_miles'], 2),
            gas_level_pct           = round(s['gas_level_pct'], 1),
            driver_fatigue_level    = round(s['driver_fatigue_level'], 2),
            speed_mph               = round(s['speed_mph'], 1),
            trip_duration_minutes   = round(s['trip_duration_minutes'], 1),
            weather                 = s['weather'],
            traffic                 = s['traffic'],
            heart_rate_bpm          = round(s['heart_rate_bpm'], 1),
            last_break_minutes_ago  = round(s['last_break_minutes_ago'], 1),
            outside_temp_f          = round(s['outside_temp_f'], 1),
            is_night_driving        = s['is_night_driving'],
            # --- Target ---
            suggestion_label        = label,
            suggestion_name         = SUGGESTION_LABELS[label],
            # --- Noisy normalised values (what the SNN actually sees) ---
            norm_distance   = round(float(np.clip(norm_dist + rng.normal(0, noise_std), 0, 1)), 4),
            norm_gas        = round(float(np.clip(norm_gas  + rng.normal(0, noise_std), 0, 1)), 4),
            norm_fatigue    = round(float(np.clip(norm_fat  + rng.normal(0, noise_std), 0, 1)), 4),
            norm_speed      = round(float(np.clip(norm_spd  + rng.normal(0, noise_std), 0, 1)), 4),
            norm_trip_min   = round(float(np.clip(norm_trip + rng.normal(0, noise_std), 0, 1)), 4),
            norm_heart_rate = round(float(np.clip(norm_hr   + rng.normal(0, noise_std), 0, 1)), 4),
            norm_last_break = round(float(np.clip(norm_brk  + rng.normal(0, noise_std), 0, 1)), 4),
            norm_temp_f     = round(float(np.clip(norm_tmp  + rng.normal(0, noise_std), 0, 1)), 4),
        ))

    fieldnames = list(rows[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print summary
    labels = [r['suggestion_label'] for r in rows]
    print(f"\nWrote {num_samples} rows to: {output_path}")
    print(f"Columns: {len(fieldnames)}")
    print("\nClass distribution:")
    for i, name in enumerate(SUGGESTION_LABELS):
        count = labels.count(i)
        bar   = '#' * (count // 5)
        print(f"  [{i:2d}] {name:<20s}  {count:4d}  {bar}")

    print("\nSample rows:")
    for r in rows[:5]:
        print(f"  {r['day_name']} {r['hour']:02d}:{r['minute']:02d}  "
              f"dest={r['destination_type']:<12s}  "
              f"dist={r['distance_to_dest_miles']:5.1f}mi  "
              f"gas={r['gas_level_pct']:5.1f}%  "
              f"fatigue={r['driver_fatigue_level']:4.1f}  "
              f"-> [{r['suggestion_label']}] {r['suggestion_name']}")

    print(f"\nDone. Open {output_path} in Excel, Google Sheets, or any CSV viewer.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export driving assistant dataset to CSV')
    parser.add_argument('--output',  default='driving_assistant_dataset.csv', help='Output CSV filename')
    parser.add_argument('--samples', type=int, default=1000,  help='Number of rows (default 1000)')
    parser.add_argument('--seed',    type=int, default=42,    help='Random seed (default 42)')
    args = parser.parse_args()

    generate_csv(num_samples=args.samples, seed=args.seed, output_path=args.output)