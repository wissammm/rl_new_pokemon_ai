from pkmn_rl_arena.data import pokemon_data
from .battle_core import BattleCore

from typing import Dict

import pandas as pd


class ObservationManager:
    """
    Manages extraction and formatting of observations from the battle state.
    """

    def __init__(self, battle_core: BattleCore):
        self.battle_core = battle_core

    def get_observations(self) -> Dict[str, pd.DataFrame]:
        """Get observations for both agents"""
        observations = {}

        # Get team data for both agents
        player_data = self.battle_core.read_team_data("player")
        enemy_data = self.battle_core.read_team_data("enemy")

        # Convert to pandas DataFrames
        observations["player"] = pokemon_data.to_pandas_team_dump_data(player_data)
        observations["enemy"] = pokemon_data.to_pandas_team_dump_data(enemy_data)

        return observations

    def get_observation_space_size(self) -> int:
        """Get the size of the observation space (to be implemented)"""
        return None
