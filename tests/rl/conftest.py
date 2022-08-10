import random
from typing import Callable

import pytest

from rl.state import State


metric: Callable[[], int] = lambda : random.randint(-120, -80)

@pytest.fixture(scope='function')
def state() -> State:
    _state = State(max_cells=6, max_ues=10)
    inications = [
        {'ue_id': '0000', 'serving_cell': 'A', 'cell_metrics': {'A': metric(), 'B': metric(), 'C': metric()}},
        {'ue_id': '0001', 'serving_cell': 'B', 'cell_metrics': {'B': metric(), 'C': metric(), 'D': metric()}},
        {'ue_id': '0002', 'serving_cell': 'C', 'cell_metrics': {'C': metric(), 'D': metric(), 'E': metric()}},
        {'ue_id': '0003', 'serving_cell': 'D', 'cell_metrics': {'D': metric(), 'E': metric(), 'F': metric()}},
        {'ue_id': '0004', 'serving_cell': 'E', 'cell_metrics': {'E': metric(), 'F': metric(), 'A': metric()}},
        {'ue_id': '0005', 'serving_cell': 'F', 'cell_metrics': {'F': metric(), 'A': metric(), 'B': metric()}},
        {'ue_id': '0006', 'serving_cell': 'A', 'cell_metrics': {'A': metric(), 'B': metric(), 'C': metric()}},
        {'ue_id': '0007', 'serving_cell': 'B', 'cell_metrics': {'B': metric(), 'C': metric(), 'D': metric()}},
        {'ue_id': '0008', 'serving_cell': 'C', 'cell_metrics': {'C': metric(), 'D': metric(), 'E': metric()}},
        {'ue_id': '0009', 'serving_cell': 'E', 'cell_metrics': {'E': metric(), 'F': metric(), 'A': metric()}},
    ]
    for indication in inications:
        _state.attach_ue(**indication)
    return _state
