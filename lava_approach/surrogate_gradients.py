import numpy as np
from lava.proc.io.source import RingBuffer
from lava.proc.dense.process import Dense
from lava.proc.lif.process import LIF
from lava.proc.monitor.process import Monitor
from lava.magma.core.run_conditions import RunSteps
from lava.magma.core.run_configs import Loihi1SimCfg

from lava_approach.model_parameters import Model_Params
from lava_approach.learning import feedback_to_reward, policy_loss_and_grad

max_firing_rate = 500.0
time_step = 1.0


def rate_encode(rng, x, steps: int):
    x = np.asarray(x, np.float32).ravel()
    scale = float(np.max(np.abs(x)))

    if scale > 1e-12:
        norm = np.abs(x) / scale
    else:
        norm = np.zeros_like(x)

    prob_spiking = np.clip(
        norm * max_firing_rate * (time_step / 1000.0),
        0.0,
        1.0,
    )
    spikes = rng.random((steps, x.size)) < prob_spiking
    return spikes.astype(np.int32)


def forward_hidden_and_output(model, x, params: Model_Params):
    rng = getattr(model, "rng", np.random.default_rng(0))
    x = np.asarray(x, np.float32).ravel()

    spikes_cf = rate_encode(rng, x, params.steps).T

    input_size = int(params.input_size)
    hidden_size = int(params.hidden_layers[0])
    output_size = int(params.output_size)

    src = RingBuffer(data=spikes_cf)

    hidden_synapses = Dense(
        shape=(hidden_size, input_size),
        weights=model.Weight_input_hidden,
    )
    hidden_LIF = LIF(shape=(hidden_size,))

    output_synapses = Dense(
        shape=(output_size, hidden_size),
        weights=model.Weight_hidden_output,
    )
    output_LIF = LIF(shape=(output_size,))

    hidden_synapses.s_in.connect_from(src.s_out)
    hidden_LIF.a_in.connect_from(hidden_synapses.a_out)
    output_synapses.s_in.connect_from(hidden_LIF.s_out)
    output_LIF.a_in.connect_from(output_synapses.a_out)

    mon_hid = Monitor()
    mon_out = Monitor()
    mon_hid.probe(target=hidden_LIF.s_out, num_steps=params.steps)
    mon_out.probe(target=output_LIF.s_out, num_steps=params.steps)

    output_LIF.run(
        condition=RunSteps(num_steps=params.steps),
        run_cfg=Loihi1SimCfg(select_tag="floating_pt"),
    )

    data_hid = mon_hid.get_data()
    data_out = mon_out.get_data()

    output_LIF.stop()
    mon_hid.stop()
    mon_out.stop()

    key_hidden = next(iter(data_hid))
    key_output = next(iter(data_out))

    s_hidden = data_hid[key_hidden]["s_out"]
    s_out = data_out[key_output]["s_out"]

    hidden_rates = s_hidden.sum(axis=0).astype(np.float32) / float(params.steps)
    out_rates = s_out.sum(axis=0).astype(np.float32) / float(params.steps)

    denom = float(np.max(out_rates) + 1e-8)
    out_rates = out_rates / denom
    return hidden_rates, out_rates


def surrogate_update(model, x, chosen_idx: int, feedback: str, params: Model_Params, lr: float = 1e-2,):
    reward = feedback_to_reward(feedback)

    if reward == 0.0:
        return 0.0

    hidden_rates, out_rates = forward_hidden_and_output(model, x, params)

    loss, grad_out = policy_loss_and_grad(out_rates, chosen_idx, reward)

    grad_W = np.outer(grad_out, hidden_rates).astype(model.Weight_hidden_output.dtype)

    model.Weight_hidden_output -= lr * grad_W

    return float(loss)
