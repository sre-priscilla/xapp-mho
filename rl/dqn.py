import random
from typing import List, Tuple
from dataclasses import dataclass

import torch
import numpy as np
from torch import Tensor
from torch.optim import SGD
from torch.nn import MSELoss

from .gnn import GNN
from .state import State


@dataclass
class Transition:
    prev: Tuple[np.ndarray, np.ndarray, np.ndarray]
    curr: Tuple[np.ndarray, np.ndarray, np.ndarray]
    reward: float


class DQN:

    def __init__(self, n_cells: int, n_ues: int, epsilon: float, gnn_dimension: int,
        learning_rate: float, learning_frequency: int, memory_capacity: int):

        self.n_cells = n_cells
        self.n_ues = n_ues
        self.epsilon = epsilon

        self.gnn_online = GNN(n_cells, n_ues, gnn_dimension)
        self.gnn_target = GNN(n_cells, n_ues, gnn_dimension)
        
        self.learning_count = 0
        self.learning_rate = learning_rate
        self.learning_frequency = learning_frequency

        self.memory_count = 0
        self.memory: List[Transition] = []   
        self.memory_capacity = memory_capacity
        

        self.optimizer = SGD(self.gnn_online.parameters(), lr=learning_rate)
        self.loss_function = MSELoss()

    def action(self, state: State) -> np.ndarray:
        actions: List[np.ndarray] = state.actions
        if np.random.uniform() >= self.epsilon:
            return random.choice(actions)
        else:
            q_values = [
                self.gnn_online.forward(
                    state.X_cl_1,
                    state.X_cl_2,
                    state.X_ue,
                    state.A_cl,
                    state.A_ue
                )
                for action in actions
            ]
            return actions[torch.max(q_values)[1]]



    def cache(self, transition: Transition):
        self.memory[self.memory_count % self.memory_capacity] = transition

    def learn(self):
        if self.learning_count % self.learning_frequency:
            self.gnn_target.load_state_dict(self.gnn_online.state_dict())
        self.learning_count += 1

