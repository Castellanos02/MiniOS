#!/usr/bin/env python3
"""
Driving Assistant Use Case Dataset Generator
============================================
Generates a realistic 1000-row dataset for MiniOS CarPlay-style
neuromorphic assistant.  The assistant observes driving context and
emits a proactive suggestion (the TARGET class).

Features (16 total)
-------------------
  0  hour                    0-23  (int, normalized)
  1  time_of_day_enc         0-3   night/morning/afternoon/evening
  2  day_of_week             0-6   Mon=0 ... Sun=6
  3  is_weekend              0/1
  4  destination_type_enc    0-7   (work/home/gas/grocery/restaurant/
                                    hospital/gym/school)
  5  distance_to_dest_miles  0-100  continuous + noise
  6  gas_level_pct           0-100  continuous + noise
  7  driver_fatigue_level    0-10   continuous + noise
  8  speed_mph               0-90   continuous + noise
  9  trip_duration_minutes   0-180  continuous + noise
  10 weather_enc             0-3   clear/rain/snow/fog
  11 traffic_enc             0-2   low/medium/high
  12 heart_rate_bpm          50-120 continuous + noise
  13 last_break_minutes_ago  0-180  continuous + noise
  14 outside_temp_f         -10-110 continuous + noise
  15 is_night_driving        0/1

Target (suggestion_label)
-------------------------
  0  no_action           Everything nominal -- no intervention needed
  1  take_break_now      Critical fatigue -- stop immediately
  2  take_break_soon     Moderate fatigue building -- plan a rest stop
  3  refuel_now          Gas <= 10% and far from dest
  4  refuel_soon         Gas 10-25%, dest is not a gas station
  5  speed_alert         Significantly over safe speed for conditions
  6  weather_warning     Hazardous weather -- slow down / reroute
  7  route_to_gas        Gas low, reroute to station
  8  food_break          Long trip, low blood-sugar window
  9  arrived_soon        < 2 miles from destination
  10 coffee_suggestion   Mild fatigue, long trip ahead
  11 rest_area_ahead     Driver tired on highway, rest area nearby

Split helpers
-------------
  get_splits(X, y, mode='70-20-10')  -> (X_train, X_val, X_test, ...)
  get_splits(X, y, mode='60-20-20')  -> (X_train, X_val, X_test, ...)
"""

import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader

# ------------------------------------------------------------------ #
#  Constants                                                           #
# ------------------------------------------------------------------ #

NUM_SAMPLES = 1000
NOISE_STD   = 0.03   # std of Gaussian noise added to normalised features

DESTINATION_TYPES = [
    'work', 'home', 'gas_station', 'grocery',
    'restaurant', 'hospital', 'gym', 'school',
]

WEATHER_TYPES  = ['clear', 'rain', 'snow', 'fog']
TRAFFIC_TYPES  = ['low', 'medium', 'high']

SUGGESTION_LABELS = [
    'no_action',         # 0
    'take_break_now',    # 1
    'take_break_soon',   # 2
    'refuel_now',        # 3
    'refuel_soon',       # 4
    'speed_alert',       # 5
    'weather_warning',   # 6
    'route_to_gas',      # 7
    'food_break',        # 8
    'arrived_soon',      # 9
    'coffee_suggestion', # 10
    'rest_area_ahead',   # 11
]

NUM_FEATURES = 16   # keep in sync with model input_size
NUM_CLASSES  = len(SUGGESTION_LABELS)

# ------------------------------------------------------------------ #
#  Raw scenario generator                                              #
# ------------------------------------------------------------------ #

def _sample_scenario(rng: np.random.Generator) -> dict:
    """Draw one random but internally-consistent driving scenario."""

    hour        = int(rng.integers(0, 24))
    minute      = int(rng.integers(0, 60))
    day_of_week = int(rng.integers(0, 7))
    is_weekend  = int(day_of_week >= 5)

    # Time-of-day bucket: 0=night 1=morning 2=afternoon 3=evening
    if   5  <= hour < 12: tod = 1
    elif 12 <= hour < 17: tod = 2
    elif 17 <= hour < 22: tod = 3
    else:                  tod = 0   # night

    is_night_driving = int(tod == 0 or hour >= 21)

    dest_idx  = int(rng.integers(0, len(DESTINATION_TYPES)))
    dest_type = DESTINATION_TYPES[dest_idx]

    # Realistic distance distribution
    distance = float(np.clip(rng.exponential(scale=12), 0.2, 100))

    # Gas level -- sometimes low to create interesting cases
    gas_low  = rng.random() < 0.20
    gas_level = float(rng.uniform(2, 18) if gas_low else rng.uniform(15, 100))

    # Fatigue rises with hour and trip length
    base_fatigue = (hour - 6) / 18 * 4 if 6 <= hour <= 24 else 2
    trip_minutes = float(np.clip(rng.exponential(scale=35), 1, 180))
    fatigue = float(np.clip(
        base_fatigue + trip_minutes / 60 * 2 + rng.uniform(-1, 2),
        0, 10,
    ))

    speed = float(np.clip(rng.normal(55, 15), 0, 90))

    weather_idx = int(rng.choice(
        [0, 1, 2, 3], p=[0.60, 0.25, 0.08, 0.07]
    ))
    weather = WEATHER_TYPES[weather_idx]

    traffic_idx = int(rng.choice([0, 1, 2], p=[0.35, 0.40, 0.25]))

    # Heart rate correlates with fatigue + stress
    heart_rate = float(np.clip(
        65 + fatigue * 3 + rng.normal(0, 6), 50, 130
    ))

    last_break = float(np.clip(rng.exponential(scale=45), 0, 180))

    temp_f = float(rng.uniform(-10, 110))

    return dict(
        hour=hour,
        minute=minute,
        time_of_day_enc=tod,
        day_of_week=day_of_week,
        is_weekend=is_weekend,
        destination_type_enc=dest_idx,
        destination_type=dest_type,
        distance_to_dest_miles=distance,
        gas_level_pct=gas_level,
        driver_fatigue_level=fatigue,
        speed_mph=speed,
        trip_duration_minutes=trip_minutes,
        weather_enc=weather_idx,
        weather=weather,
        traffic_enc=traffic_idx,
        heart_rate_bpm=heart_rate,
        last_break_minutes_ago=last_break,
        outside_temp_f=temp_f,
        is_night_driving=is_night_driving,
    )


# ------------------------------------------------------------------ #
#  Rule-based labeller                                                 #
# ------------------------------------------------------------------ #

def _label_scenario(s: dict) -> int:
    """
    Priority-ordered rules that mirror real CarPlay assistant logic.
    Returns the integer suggestion label.
    """
    dist   = s['distance_to_dest_miles']
    gas    = s['gas_level_pct']
    fat    = s['driver_fatigue_level']
    spd    = s['speed_mph']
    weather= s['weather']
    brk    = s['last_break_minutes_ago']
    trip   = s['trip_duration_minutes']
    dest   = s['destination_type']
    hr     = s['heart_rate_bpm']
    tod    = s['time_of_day_enc']
    night  = s['is_night_driving']

    # --- highest priority: safety-critical ---

    # Critical fatigue: high fatigue + long time since break OR night + high hr
    if fat >= 7.5 or (fat >= 6 and brk > 90) or (night and hr > 105):
        return 1  # take_break_now

    # Severe weather
    if weather in ('snow', 'fog') and spd > 45:
        return 6  # weather_warning

    # Speed alert: too fast for conditions
    safe_speed = 70 if weather == 'clear' else 55 if weather == 'rain' else 35
    if spd > safe_speed + 10:
        return 5  # speed_alert

    # --- fuel ---

    if gas <= 10:
        if dest == 'gas_station':
            return 3  # refuel_now (already heading there but critically low)
        return 7      # route_to_gas (reroute)

    if gas <= 25 and dest != 'gas_station':
        return 4  # refuel_soon

    # --- arrival ---
    if dist < 2:
        return 9  # arrived_soon

    # --- moderate fatigue ---
    if fat >= 5.5 or (brk > 75 and trip > 60):
        if night:
            return 1   # nighttime fatigue is more dangerous
        return 2       # take_break_soon

    # --- food / coffee ---
    if trip > 90 and tod in (1, 2):   # morning/afternoon long drive
        return 8   # food_break

    if fat >= 3.5 and trip > 45:
        return 10  # coffee_suggestion

    # --- rest area (highway, tired, long trip) ---
    if brk > 60 and trip > 70 and spd > 40:
        return 11  # rest_area_ahead

    # --- mild weather caution ---
    if weather in ('rain',) and spd > 60:
        return 6  # weather_warning (rain caution)

    return 0   # no_action


# ------------------------------------------------------------------ #
#  Feature builder                                                     #
# ------------------------------------------------------------------ #

def _build_feature_vector(s: dict) -> list:
    """
    Normalise raw scenario values into [0, 1] (mostly) float features.
    Order must stay in sync with NUM_FEATURES and the docstring above.
    """
    return [
        s['hour']                    / 23.0,          # 0  hour
        s['time_of_day_enc']         /  3.0,          # 1  time_of_day_enc
        s['day_of_week']             /  6.0,          # 2  day_of_week
        float(s['is_weekend']),                       # 3  is_weekend
        s['destination_type_enc']    /  7.0,          # 4  destination_type_enc
        s['distance_to_dest_miles']  / 100.0,         # 5  distance_to_dest
        s['gas_level_pct']           / 100.0,         # 6  gas_level_pct
        s['driver_fatigue_level']    /  10.0,         # 7  driver_fatigue_level
        s['speed_mph']               /  90.0,         # 8  speed_mph
        s['trip_duration_minutes']   / 180.0,         # 9  trip_duration_min
        s['weather_enc']             /  3.0,          # 10 weather_enc
        s['traffic_enc']             /  2.0,          # 11 traffic_enc
        (s['heart_rate_bpm'] - 50)   /  80.0,         # 12 heart_rate_bpm
        s['last_break_minutes_ago']  / 180.0,         # 13 last_break_min_ago
        (s['outside_temp_f'] + 10)   / 120.0,         # 14 outside_temp_f
        float(s['is_night_driving']),                 # 15 is_night_driving
    ]


# ------------------------------------------------------------------ #
#  Public API: generate_use_case_training_data                        #
# ------------------------------------------------------------------ #

def generate_use_case_training_data(
    num_samples: int = NUM_SAMPLES,
    seed: int = 42,
    noise_std: float = NOISE_STD,
):
    """
    Generate the driving assistant dataset.

    Parameters
    ----------
    num_samples : int
        Number of rows to generate (default 1000).
    seed : int
        Random seed for reproducibility.
    noise_std : float
        Standard deviation of Gaussian noise added to *continuous*
        normalised features (indices 5-9, 12-14).  Set to 0 to disable.

    Returns
    -------
    X : np.ndarray  shape (num_samples, NUM_FEATURES)  float32
    y : np.ndarray  shape (num_samples,)               int64
    scenarios : list[dict]   raw human-readable dicts for inspection
    """
    rng = np.random.default_rng(seed)

    X_list, y_list, scenarios = [], [], []

    for _ in range(num_samples):
        s     = _sample_scenario(rng)
        label = _label_scenario(s)
        feat  = _build_feature_vector(s)

        X_list.append(feat)
        y_list.append(label)
        scenarios.append({**s, 'suggestion': SUGGESTION_LABELS[label], 'label': label})

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int64)

    # Add Gaussian noise to continuous features only (indices 5-9, 12-14)
    if noise_std > 0:
        continuous_idx = [5, 6, 7, 8, 9, 12, 13, 14]
        noise = rng.normal(0, noise_std, size=(num_samples, len(continuous_idx))).astype(np.float32)
        X[:, continuous_idx] = np.clip(X[:, continuous_idx] + noise, 0.0, 1.0)

    return X, y, scenarios


# ------------------------------------------------------------------ #
#  Train / Val / Test split helper                                     #
# ------------------------------------------------------------------ #

def get_splits(
    X: np.ndarray,
    y: np.ndarray,
    mode: str = '70-20-10',
    seed: int = 0,
):
    """
    Split dataset into (train, val, test) subsets.

    Parameters
    ----------
    X, y  : arrays returned by generate_use_case_training_data
    mode  : '70-20-10'  or  '60-20-20'
    seed  : shuffle seed

    Returns
    -------
    X_train, X_val, X_test, y_train, y_val, y_test
    """
    ratios = {
        '70-20-10': (0.70, 0.20, 0.10),
        '60-20-20': (0.60, 0.20, 0.20),
    }
    if mode not in ratios:
        raise ValueError(f"mode must be one of {list(ratios.keys())}")

    tr, va, te = ratios[mode]
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))

    n_tr = int(len(X) * tr)
    n_va = int(len(X) * va)

    tr_idx = idx[:n_tr]
    va_idx = idx[n_tr:n_tr + n_va]
    te_idx = idx[n_tr + n_va:]

    return (
        X[tr_idx], X[va_idx], X[te_idx],
        y[tr_idx], y[va_idx], y[te_idx],
    )


def get_dataloaders(
    X: np.ndarray,
    y: np.ndarray,
    mode: str = '70-20-10',
    batch_size: int = 32,
    seed: int = 0,
):
    """
    Convenience wrapper: returns three DataLoaders (train, val, test).
    """
    X_tr, X_va, X_te, y_tr, y_va, y_te = get_splits(X, y, mode, seed)

    def _make(Xa, ya, shuffle):
        ds = TensorDataset(
            torch.tensor(Xa, dtype=torch.float32),
            torch.tensor(ya, dtype=torch.long),
        )
        return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)

    return _make(X_tr, y_tr, True), _make(X_va, y_va, False), _make(X_te, y_te, False)


# ------------------------------------------------------------------ #
#  Legacy stubs (keep old callers from breaking)                       #
# ------------------------------------------------------------------ #

# Old name used in several training scripts
USE_CASES = {}       # no longer used but imported by some files
ACTIVITY_LABELS = SUGGESTION_LABELS   # alias


class UserProfile:
    """Thin stub retained for backwards compatibility."""
    def __init__(self):
        self.preferences = {}
        self.history = {'accepts': {}, 'rejects': {}}

    def update_preference(self, category, choice, accepted):
        if accepted:
            self.preferences[category] = choice

    def get_preference(self, category):
        return self.preferences.get(category, 'default')


# ------------------------------------------------------------------ #
#  Quick smoke-test                                                    #
# ------------------------------------------------------------------ #

if __name__ == '__main__':
    print('=' * 70)
    print('DRIVING ASSISTANT USE CASE DATASET -- GENERATOR SMOKE TEST')
    print('=' * 70)

    X, y, scenarios = generate_use_case_training_data(num_samples=1000, seed=42)

    print(f'\n  Generated {len(X)} samples')
    print(f'  Feature dimensions : {X.shape[1]}  (NUM_FEATURES={NUM_FEATURES})')
    print(f'  Suggestion classes : {NUM_CLASSES}')

    # Class distribution
    print('\nClass distribution:')
    for i, name in enumerate(SUGGESTION_LABELS):
        count = int((y == i).sum())
        bar   = '#' * (count // 5)
        print(f'  [{i:2d}] {name:<20s}  {count:4d}  {bar}')

    # Sample scenarios
    print('\n' + '=' * 70)
    print('SAMPLE SCENARIOS')
    print('=' * 70)
    for i in range(8):
        s = scenarios[i]
        dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][s['day_of_week']]
        print(
            f"\n  #{i+1}  {dow} {s['hour']:02d}:{s['minute']:02d}  |"
            f"  Dest: {s['destination_type']:<12s}"
            f"  {s['distance_to_dest_miles']:.1f} mi  |"
            f"  Gas: {s['gas_level_pct']:.0f}%  |"
            f"  Fatigue: {s['driver_fatigue_level']:.1f}/10  |"
            f"  Weather: {s['weather']}"
        )
        print(f"-> Suggestion: [{s['label']}] {s['suggestion']}")

    # Feature stats
    print('\nFeature value ranges (after noise):')
    feat_names = [
        'hour','time_of_day','day_of_week','is_weekend','dest_type',
        'distance','gas_level','fatigue','speed','trip_minutes',
        'weather','traffic','heart_rate','last_break','temp_f','night',
    ]
    for j, name in enumerate(feat_names):
        col = X[:, j]
        print(f'  {name:<18s}  min={col.min():.3f}  max={col.max():.3f}  '
              f'mean={col.mean():.3f}  std={col.std():.3f}')

    # Split test
    print('\n70-20-10 split:')
    X_tr, X_va, X_te, y_tr, y_va, y_te = get_splits(X, y, '70-20-10')
    print(f'  train={len(X_tr)}  val={len(X_va)}  test={len(X_te)}')

    print('\n60-20-20 split:')
    X_tr, X_va, X_te, y_tr, y_va, y_te = get_splits(X, y, '60-20-20')
    print(f'  train={len(X_tr)}  val={len(X_va)}  test={len(X_te)}')

    print('\n  Dataset ready for training!')
    print('=' * 70)