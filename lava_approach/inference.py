import numpy as np

def inference(model, x, params=None):
    x = np.asarray(x, np.float32).ravel()
    return model.forward_rates(x)
