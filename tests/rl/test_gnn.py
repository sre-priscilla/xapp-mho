from typing import Tuple

import torch
import numpy as np

from rl.gnn import GNN
from rl.state import Inputs, State

def test_gnn(state: State):
    inputs: Inputs = state.inputs
    print(inputs)

    gnn = GNN(n_cells=6, n_ues=10, dimension=8)
    qvalue = gnn.forward(
        torch.from_numpy(inputs.X_cl_1.astype(np.float64)),
        torch.from_numpy(inputs.X_cl_2.astype(np.float64)),
        torch.from_numpy(inputs.X_ue.astype(np.float64)),
        torch.from_numpy(inputs.A_cl.astype(np.float64)),
        torch.from_numpy(inputs.A_ue.astype(np.float64))
    )
    print(qvalue.detach().numpy()[0][0])

