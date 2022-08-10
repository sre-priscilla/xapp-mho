from typing import Tuple
from dataclasses import dataclass

from .state import State


@dataclass
class Env:

    prev: State
    curr: State
    
    def step(action) -> Tuple[State, float]:
        pass

    def reset():
        pass
