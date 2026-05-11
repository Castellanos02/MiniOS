class Model_Params:
    def __init__(
        self,
        input_size=None,
        hidden_layers=None,
        neuron_type="LIF",
        surrogate_gradient="Piecewise Linear",
        output_size=2,
        readout_interpretation="Spike Rate",
        steps=10,
    ):
        self.input_size = None if input_size is None else int(input_size)

        if hidden_layers is None:
            self.hidden_layers = [64]
        else:
            self.hidden_layers = [int(h) for h in list(hidden_layers)]

        self.neuron_type = neuron_type
        self.surrogate_gradient = surrogate_gradient
        self.output_size = int(output_size)
        self.readout_interpretation = readout_interpretation
        self.steps = int(steps)

    def __repr__(self) -> str:
        return (
            f"Model_Params(input_size={self.input_size}, "
            f"hidden_layers={self.hidden_layers}, "
            f"neuron_type={self.neuron_type!r}, "
            f"surrogate_gradient={self.surrogate_gradient!r}, "
            f"output_size={self.output_size}, "
            f"readout_interpretation={self.readout_interpretation!r}, "
            f"steps={self.steps})"
        )
