from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class TurnType(Enum):
    """Enumeration for different turn types"""

    CREATE_TEAM = "create_team"  # Initial team creation
    GENERAL = "general"  # Both players act simultaneously
    PLAYER = "player"  # Only player acts
    ENEMY = "enemy"  # Only enemy acts
    DONE = "done"  # Battle is finished


@dataclass
class BattleState:
    """Represents the current state of the battle"""

    current_step: int = 0
    episode_done: bool = False
    current_turn: Optional[TurnType] = None
    waiting_for_action: bool = False
    episode_steps: int = 0
    pending_actions: Dict[str, Optional[int]] = None

    def __post_init__(self):
        if self.pending_actions is None:
            self.pending_actions = {"player": None, "enemy": None}
