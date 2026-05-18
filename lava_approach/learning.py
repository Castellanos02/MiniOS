import numpy as np

def feedback_to_reward(feedback: str) -> float:
    feedback = feedback.lower().strip()
    if feedback == "accept":
        return 1.0
    elif feedback == "reject":
        return -1.0
    elif feedback == "ignore":
        return 0.0
    else:
        raise ValueError(f"Unknown feedback: {feedback!r}")


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits, np.float32).ravel()
    shifted = logits - np.max(logits)
    exps = np.exp(shifted)
    return exps / np.sum(exps)


def policy_loss_and_grad(out_rates: np.ndarray, action_idx: int, reward: float):
    probs = softmax(out_rates)
    num_actions = probs.shape[0]

    p_a = probs[action_idx]
    loss = -reward * np.log(p_a + 1e-8)

    one_hot = np.zeros(num_actions, dtype=np.float32)
    one_hot[action_idx] = 1.0

    grad_out = -reward * (one_hot - probs)
    return float(loss), grad_out
