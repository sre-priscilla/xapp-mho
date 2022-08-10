from typing import List, Dict, Tuple
from dataclasses import dataclass
from typing_extensions import Self

import torch
import numpy as np
import pandas as pd

@dataclass
class Inputs:
    X_cl_1: np.ndarray
    X_cl_2: np.ndarray
    X_ue: np.ndarray
    A_cl: np.ndarray
    A_ue: np.ndarray
    
    def as_list(self) -> List[np.ndarray]:
        return [self.X_cl_1, self.X_cl_2, self.X_ue, self.A_cl, self.A_ue]


class State:
    G_cl: pd.DataFrame
    G_ue: pd.DataFrame

    def __init__(self, max_cells: int, max_ues: int):
        self.max_cells = max_cells
        self.max_ues = max_ues

        self.G_cl = pd.DataFrame()
        self.G_ue = pd.DataFrame()

        self.connections: Dict[str, str] = {}

    @property
    def N(self) -> int:
        '''
        count of cells
        '''
        return len(self.G_cl.index)

    @property
    def M(self) -> int:
        '''
        count of ues
        '''
        return len(self.G_ue.index)

    @property
    def A_cl(self) -> np.ndarray:
        return self.G_cl.values

    @property
    def A_ue(self) -> np.ndarray:
        return np.array([
            [
                (1 if self.connections[ue_id] == cell_id else 0)
                for ue_id in self.G_ue.index
            ]
            for cell_id in self.G_ue.columns
        ])

    @property
    def C(self) -> np.ndarray:
        return self.G_ue.values.T

    @property
    def R(self) -> np.ndarray:
        # ues count on every cells
        C_abs: np.ndarray = self.A_ue.sum(axis=1, keepdims=True)
        return self.C / np.tile(C_abs, self.M)

    @property
    def inputs(self) -> Inputs:
        C, R = self.C, self.R
        A_cl, A_ue = self.A_cl, self.A_ue
        N_1, M_1 = np.ones((self.N, 1)), np.ones((self.M, 1))

        X_cl_1 = np.hstack((A_cl @ R @ M_1, R @ M_1))
        X_cl_2 = np.hstack((A_ue @ R.T @ N_1, C @ M_1))
        X_ue = np.hstack((C.T @ N_1, R.T @ N_1))

        return Inputs(X_cl_1, X_cl_2, X_ue, A_cl, A_ue)

    @property
    def actions() -> List:
        pass

    def attach_ue(self, ue_id: str, serving_cell: str, cell_metrics: Dict[str, int]):
        if serving_cell not in cell_metrics:
            return
        for cell_id, metric in cell_metrics.items():
            if cell_id not in self.G_cl.columns and self.N < self.max_cells:
                self.G_cl[cell_id] = 0
                self.G_ue[cell_id] = 0
                self.G_cl.loc[cell_id] = 0  
        for cell_id in cell_metrics:
            if cell_id in self.G_cl.columns:
                self.G_cl.loc[serving_cell][cell_id] = 1
        
        if ue_id not in self.connections and self.M == self.max_ues:
            return   
        self.G_ue.loc[ue_id] = 0
        self.connections[ue_id] = serving_cell
        for cell_id, metric in cell_metrics.items():
            self.G_ue.loc[ue_id][cell_id] = metric
        

    def detach_ue(self, ue_id: str):
        self.G_ue.iloc[ue_id] = 0
        self.connections[ue_id] = None


