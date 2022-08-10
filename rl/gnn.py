from typing import List

import torch
from torch import nn
from torch import Tensor
import torch.nn.functional as F


class GNN(nn.Module):

    def __init__(self, n_cells: int, n_ues: int, dimension: int):
        super(GNN, self).__init__()

        self.n_cells = n_cells
        self.n_ues = n_ues
        self.dimension = dimension
        
        self.W_1: List[nn.Linear] = [
            nn.Linear(2, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
        ]
        self.W_2: List[nn.Linear] = [
            nn.Linear(2, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
        ]
        self.W_3: List[nn.Linear] = [
            nn.Linear(2, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.Linear(dimension, dimension, dtype=torch.float64),
        ]
        self.Q = nn.Sequential(
            nn.Linear(dimension, dimension, dtype=torch.float64),
            nn.ReLU(),
            nn.Linear(dimension, 1, dtype=torch.float64)
        )
    
    def forward(self, X_cl_1: Tensor, X_cl_2: Tensor, X_ue: Tensor, A_cl: Tensor, A_ue: Tensor) -> Tensor:
        for l in range(4):
            H_cl: Tensor = F.relu(self.W_1[l](X_cl_1)) + F.relu(self.W_2[l](X_cl_2))
            H_ue: Tensor = F.relu(self.W_3[l](X_ue))

            X_cl_1: Tensor = torch.mm(A_cl, H_cl)
            X_cl_2: Tensor = torch.mm(A_ue, H_ue)
            X_ue: Tensor = torch.mm(A_ue.T, H_cl)
        
        N_1: Tensor = torch.ones(1, self.n_cells, dtype=torch.float64)
        return self.Q(torch.mm(N_1, H_cl))