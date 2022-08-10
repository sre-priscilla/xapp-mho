import random
from typing import Callable

from rl.state import State


def test_state(state: State):
    print(state.G_cl)
    print(state.G_ue)
    print(state.A_cl)
    print(state.A_ue)
    print(state.C)
    print(state.R)
    print(state.inputs)

