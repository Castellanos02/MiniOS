import numpy as np

from model_parameters import Model_Params
from model_creation import create_model
from personal_model import encode_input
from inference import inference
from surrogate_gradients import surrogate_update


DEFAULT_CLASS_NAMES = [
    "none",
    "remind_next_meeting",
    "play_music_default",
    "play_music_awake",
    "play_playlist",
    "play_podcast",
    "suggest_gas_station",
    "reroute_destination",
    "read_email_aloud",
    "text_contact",
    "change_location",
    "find_parking",
    "study",
    "silence_phone", 
]


class PersonalAssistant:
    def __init__(self, params: Model_Params, class_names=None):
        self.params = params
        self.class_names = (
            list(class_names) if class_names is not None else list(DEFAULT_CLASS_NAMES)
        )

        self.model = None

        self.interaction_idx = 0
        self.log = []

    def ensure_model_built(self, x_example: np.ndarray):
        if self.model is not None:
            return

        x_example = np.asarray(x_example, np.float32).ravel()
        if self.params.input_size is None:
            self.params.input_size = x_example.size

        self.model = create_model(self.params)

    def suggest(self, context_dict):

        x = encode_input(
            intent=context_dict["intent"],
            dialog_state=context_dict["dialog_state"],
            time_calendar=context_dict["time_calendar"],
            candidate=context_dict["candidate"],
        )

        self.ensure_model_built(x)

        rates = inference(self.model, x, self.params)
        rates = np.asarray(rates, np.float32).ravel()

        action_idx = int(np.argmax(rates))
        suggestion_name = self.class_names[action_idx]
        return action_idx, suggestion_name, rates

    def update_from_feedback(
        self,
        context_dict,
        action_idx: int,
        feedback: str,
        lr: float = 1e-2,
    ):
        x = encode_input(
            intent=context_dict["intent"],
            dialog_state=context_dict["dialog_state"],
            time_calendar=context_dict["time_calendar"],
            candidate=context_dict["candidate"],
        )

        self.ensure_model_built(x)

        loss = surrogate_update(
            model=self.model,
            x=x,
            chosen_idx=action_idx,
            feedback=feedback,
            params=self.params,
            lr=lr,
        )

        self.interaction_idx += 1
        self.log.append(
            {
                "t": self.interaction_idx,
                "context": context_dict,
                "action_idx": int(action_idx),
                "feedback": feedback,
                "loss": float(loss),
            }
        )

        return float(loss)
