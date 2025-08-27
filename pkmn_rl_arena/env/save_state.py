from pkmn_rl_arena import SAVE_PATH

from .battle_core import BattleCore

import os
from typing import List


class SaveStateManager:
    """
    Manages emulator save states for quick save/load functionality.
    """

    def __init__(self, battle_core: BattleCore):
        self.battle_core = battle_core
        self.save_dir = SAVE_PATH
        os.makedirs(self.save_dir, exist_ok=True)

    def save_state(self, name: str):
        """Save current state with the given name."""
        self.battle_core.save_savestate(name)

    def load_state(self, name: str) -> bool:
        """Load a saved state by name. Returns True if successful, False otherwise."""
        self.battle_core.load_savestate(name)
        self.battle_core.setup_addresses()
        self.battle_core.setup_stops()
        return True

    def list_save_states(self) -> List[str]:
        """List all available save state names (without extension)."""
        if not os.path.exists(self.save_dir):
            return []
        files = os.listdir(self.save_dir)
        return [f[:-10] for f in files if f.endswith(".savestate")]

    def has_state(self, name: str) -> bool:
        """Check if a save state with the given name exists."""
        return os.path.exists(os.path.join(self.save_dir, f"{name}.savestate"))
