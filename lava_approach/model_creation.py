import numpy as np
from lava.proc.io.source import RingBuffer
from lava.proc.dense.process import Dense
from lava.proc.lif.process import LIF
from lava.proc.monitor.process import Monitor
from lava.magma.core.run_conditions import RunSteps
from lava.magma.core.run_configs import Loihi1SimCfg

from model_parameters import Model_Params

# Max firing rate for spiking neural network (Hz)
max_firing_rate = 500.0
# RNG seed for reproducibility
seed = 0
# Simulation timestep in milliseconds
time_step = 1.0


class Process_Graph_Model:
    def __init__(self, params: Model_Params):
        self.params = params
        self.rng = np.random.default_rng(seed)

        input_size = int(self.params.input_size)
        output_size = int(self.params.output_size)
        hidden_size = int(self.params.hidden_layers[0])

        self.Weight_input_hidden = np.asarray(
            self.rng.normal(0, 0.1, size=(hidden_size, input_size)),
            dtype=np.float32,
        )
        self.Weight_hidden_output = np.asarray(
            self.rng.normal(0, 0.1, size=(output_size, hidden_size)),
            dtype=np.float32,
        )

    def rate_encode(self, x):
        x = np.asarray(x, np.float32).ravel()
        scale = float(np.max(np.abs(x)))

        if scale > 1e-12:
            norm = np.abs(x) / scale
        else:
            norm = np.zeros_like(x)

        prob_spiking = np.clip(
            norm * max_firing_rate * (time_step / 1000.0), 0.0, 1.0
        )

        spikes = self.rng.random((self.params.steps, x.size)) < prob_spiking
        return spikes.astype(np.int32)

    def forward_rates(self, x):
        x = np.asarray(x, np.float32).ravel()
        spikes_cf = self.rate_encode(x).T

        input_size = int(self.params.input_size)
        output_size = int(self.params.output_size)
        hidden_size = int(self.params.hidden_layers[0])

        # Source of spikes over time
        src = RingBuffer(data=spikes_cf)

        # Hidden layer
        hidden_synapses = Dense(
            shape=(hidden_size, input_size),
            weights=self.Weight_input_hidden,
        )
        hidden_LIF = LIF(shape=(hidden_size,))

        # Output layer
        output_synapses = Dense(
            shape=(output_size, hidden_size),
            weights=self.Weight_hidden_output,
        )
        output_LIF = LIF(shape=(output_size,))

        # Connect processes
        hidden_synapses.s_in.connect_from(src.s_out)
        hidden_LIF.a_in.connect_from(hidden_synapses.a_out)
        output_synapses.s_in.connect_from(hidden_LIF.s_out)
        output_LIF.a_in.connect_from(output_synapses.a_out)

        # Monitor output spikes
        mon_out = Monitor()
        mon_out.probe(target=output_LIF.s_out, num_steps=self.params.steps)

        # Run simulation
        output_LIF.run(
            condition=RunSteps(num_steps=self.params.steps),
            run_cfg=Loihi1SimCfg(select_tag="floating_pt"),
        )

        data = mon_out.get_data()
        output_LIF.stop()
        mon_out.stop()

        # Retrieve recorded spikes
        proc_key = next(iter(data))
        s_out = data[proc_key]["s_out"]

        counts = s_out.sum(axis=0).astype(np.float32)
        rates = counts / float(self.params.steps)

        denom = float(np.max(rates) + 1e-8)
        return rates / denom


def create_model(params: Model_Params) -> Process_Graph_Model:
    return Process_Graph_Model(params)
