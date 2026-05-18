import numpy as np

def encode_input(intent: str, dialog_state: str, time_calendar: dict, candidate: dict,) -> np.ndarray:

    feats = []

    intent_list = [
        "other",
        "music",
        "gas_request",
        "reroute",
        "meeting",
        "email",
        "text",
        "location_change",
    ]
    intent_vec = np.zeros(len(intent_list), dtype=np.float32)
    if intent in intent_list:
        intent_vec[intent_list.index(intent)] = 1.0
    feats.append(intent_vec)

    dialog_list = ["idle", "asking_user", "confirming", "followup"]
    dialog_vec = np.zeros(len(dialog_list), dtype=np.float32)
    if dialog_state in dialog_list:
        dialog_vec[dialog_list.index(dialog_state)] = 1.0
    feats.append(dialog_vec)

    hour = float(time_calendar.get("hour_of_day", 0.0)) / 24.0
    is_weekend = float(time_calendar.get("is_weekend", 0.0))
    in_commute = float(time_calendar.get("in_commute", 0.0))
    busy_now = float(time_calendar.get("busy_now", 0.0))
    feats.append(
        np.array([hour, is_weekend, in_commute, busy_now], dtype=np.float32)
    ) 

    candidate_type_list = [
        "none",
        "playlist",
        "podcast",
        "gas_station_option",
        "reroute_option",
        "meeting_option",
        "email_option",
        "text_option",
        "parking_option",
    ]
    cand_type_vec = np.zeros(len(candidate_type_list), dtype=np.float32)
    cand_type = candidate.get("suggestion", "none")
    if cand_type in candidate_type_list:
        cand_type_vec[candidate_type_list.index(cand_type)] = 1.0

    extra1 = float(candidate.get("extra1", 0.0))
    extra2 = float(candidate.get("extra2", 0.0))
    extra3 = float(candidate.get("extra3", 0.0))

    feats.append(
        np.concatenate([cand_type_vec, [extra1, extra2, extra3]]).astype(np.float32)
    )

    x = np.concatenate(feats).astype(np.float32)
    return x
