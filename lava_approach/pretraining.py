from typing import Callable, Sequence

def pretrain_on_events(
    assistant,
    events: Sequence[dict],
    build_gas_context: Callable[[dict, dict], dict],
    build_context_from_event: Callable[[dict, str], dict],
    choose_suggestion_type_for_event: Callable[[dict], str],
    default_action_for_intent: dict,
    class_names: Sequence[str],
    num_epochs: int = 20,
    lr: float = 1e-2,
):

    print(f"\nPretraining on schedule events for {num_epochs} epochs.")

    gas_action_idx = class_names.index("suggest_gas_station")

    gas_options_for_pretrain = [
        {
            "id": "gas_pre_1",
            "name": "Pretrain Gas Station 1",
            "distance_miles": 1.0,
            "price_per_gal": 4.75,
            "extra_minutes": 1.0,
        },
        {
            "id": "gas_pre_2",
            "name": "Pretrain Gas Station 2",
            "distance_miles": 1.5,
            "price_per_gal": 4.80,
            "extra_minutes": 2.0,
        },
    ]

    for epoch in range(num_epochs):
        for event in events:
            summary_lower = event["summary"].lower()

            if "gas" in summary_lower or "refuel" in summary_lower:
                gas_opt = gas_options_for_pretrain[0]
                ctx = build_gas_context(event, gas_opt)

                assistant.update_from_feedback(
                    context_dict=ctx,
                    action_idx=gas_action_idx,
                    feedback="accept",
                    lr=lr,
                )
                continue

            suggestion_type = choose_suggestion_type_for_event(event)
            ctx = build_context_from_event(event, suggestion_type=suggestion_type)
            intent = ctx["intent"]
            target_name = default_action_for_intent.get(intent, "none")
            target_idx = class_names.index(target_name)

            assistant.update_from_feedback(
                context_dict=ctx,
                action_idx=target_idx,
                feedback="accept",
                lr=lr,
            )

    print("Pretraining complete.\n")
