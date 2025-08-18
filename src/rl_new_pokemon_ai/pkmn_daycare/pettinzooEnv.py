from argparse import ArgumentError
from typing import Optional, List, Dict
from pathlib import Path

from env.core import PokemonRLCore
from pettingzoo import AECEnv
from rl_new_pokemon_ai import PATHS
from rl_new_pokemon_ai.env.core import (
    BattleCore,
    BattleState,
    ObservationManager,
    ActionManager,
    TurnManager,
    TurnType,
    EpisodeManager,
    SaveStateManager,
    PkmnTeamFactory,
)
from rl_new_pokemon_ai.utils.logging import logger
from gymnasium.spaces import Discrete
import numpy as np


class PkmnDayCare(AECEnv):
    """
    This class describes the pokemon battle environment for MARL
    It handles :
        Observation Space
        Action Space
        Rewards

    The action is structured around episodes : a whole pokemon team battle
    """

    metadata = {
        "name": "pkmn_daycare_v0.1",
    }

    def __init__(self, battle_core: BattleCore, max_steps_per_episode: int = 1000):
        # Initialize core components
        self.battle_core = battle_core
        self.observation_manager = ObservationManager(self.battle_core)
        self.action_manager = ActionManager(self.battle_core)
        self.turn_manager = TurnManager(self.battle_core, self.action_manager)
        self.episode_manager = EpisodeManager()
        self.save_state_manager = SaveStateManager(self.battle_core)
        self.team_factory = PkmnTeamFactory(PATHS["PKMN_CSV"], PATHS["MOVES_CSV"])

        # Environment configuration
        self.possible_agents = ["player", "enemy"]
        self.action_space_size = 10

        self.terminations = {agent: False for agent in self.agents}
        self.rewards = {"player": 0.0, "enemy": 0.0}
        self.total_steps = 0
        self.max_steps_per_episode = max_steps_per_episode  # Configurable

    def reset(
        self,
        seed: int | None = None,
        options: Dict[str, str] | None = None,
    ):
        """
        Reset needs to initialize the following attributes
        - agents
        - rewards
        - _cumulative_rewards
        - terminations
        - truncations
        - infos
        - agent_selection
        And must set up the environment so that render(), step(), and observe()
        can be called without issues.
        Here it sets up the state dictionary which is used by step() and the observations dictionary which is used by step() and observe()

        args:
            seed : to generate teams
            options : Dictionnary : "save_state" : path to save state
        """
        # TODO Implement seed args

        logger.info("Resetting env")

        # Load save state if provided
        if options is None:
            raise ValueError(
                'options argument is empty, cannot load save_state from options["save_state"], exiting'
            )
        elif options.get("save_state", None) is None:
            raise ValueError(
                f'"save_state" key was not found in options argument. cannot load save state.\nKeys in option : {options.keys()}.\n\nexiting'
            )

        save_state = Path(options["save_state"])
        if not self.save_state_manager.has_state(save_state):
            raise ValueError(f"Save state not found at path : {save_state} exiting.")

        loaded = self.save_state_manager.load_state(save_state)
        if not loaded:
            raise RuntimeError(f"Failed to load save state: {save_state}")

        # Reset managers
        self.rewards = {"player": 0.0, "enemy": 0.0}
        self.total_steps = 0
        self.episode_manager.reset_episode()
        self.turn_manager.reset_battle_state()
        self.terminations = {agent: False for agent in self.agents}

        # Reset team
        turn = self.turn_manager.advance_to_next_turn()
        if turn != TurnType.CREATE_TEAM:
            raise RuntimeError("Expected to start with CREATE_TEAM turn")
        player_team = self.team_factory.create_random_team(self.battle_core)
        enemy_team = self.team_factory.create_random_team(self.battle_core)

        self.battle_core.write_team_data("player", player_team)
        self.battle_core.write_team_data("enemy", enemy_team)
        self.battle_core.clear_stop_condition(turn)

        # Advance to first turn
        self.turn_manager.advance_to_next_turn()
        # Get initial observations
        self.observation_manager.get_observations()

    def step(self, actions):
        """
        step(action) takes in an action for the current agent (specified by
        agent_selection) and needs to update
        - rewards
        - _cumulative_rewards (accumulating the rewards)
        - terminations
        - truncations
        - infos
        - agent_selection (to the next agent)
        And any internal state used by observe() or render()

        Args:
            actions: Dictionary of actions for each agent

        Returns:
            observations: New observations for each agent
            rewards: Rewards for each agent (placeholder)
            done: Whether the episode is finished
            info: Additional information


        """
        # Execute actions

        # Check termination conditions
        if (
            self.turn_manager.is_battle_done()
            or self.max_steps_per_episode > self.episode_steps
        ):
            terminations = {agent: True for agent in self.agents}

        # Get observations
        # Get dummy infos (not used in this example)
        # Validate actions
        for agent, action in actions.items():
            if not self.action_manager.is_valid_action(action):
                raise ValueError(f"Invalid action {action} for agent {agent}")

        # Process turn
        turn_completed = self.turn_manager.process_turn(actions)

        if turn_completed:
            # Advance to next turn
            self.turn_manager.advance_to_next_turn()

        # Get new observations
        observations = self.observation_manager.get_observations()

        # Calculate rewards (placeholder)
        rewards = {"player": 0.0, "enemy": 0.0}

        # Check if episode is done
        battle_done = self.turn_manager.is_battle_done()
        episode_done = self.episode_manager.is_episode_done(battle_done)

        # Update episode
        self.episode_manager.update_episode(rewards)

        # Prepare info
        info = {
            "current_turn": self.turn_manager.get_current_turn(),
            "battle_done": battle_done,
            "episode_info": self.episode_manager.get_episode_info(),
        }

        return observations, rewards, episode_done, info

    def render(self):
        pass

    def observe(self, agent):
        """
        Observe should return the observation of the specified agent. This function
        should return a sane observation (though not necessarily the most up to date possible)
        at any time after reset() is called.
        """
        # observation of one agent is the previous state of the other
        return np.array(self.observations[agent])

    # Observation space should be defined here.
    # lru_cache allows observation and action spaces to be memoized, reducing clock cycles required to get each agent's space.
    # If your spaces change over time, remove this line (disable caching).
    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        # gymnasium spaces are defined and documented here: https://gymnasium.farama.org/api/spaces/
        return Discrete(4)

    # Action space should be defined here.
    # If your spaces change over time, remove this line (disable caching).
    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        # We can seed the action space to make the environment deterministic.
        #
        # retrieve attacks within csv, the action space must be :
        # 1. All pkmn of the team with USEFUL stats shown
        # 2. Current moveset with stats as described from the csv
        return Discrete(3, seed=self.np_random_seed)

    def close():
        """
        Close should release any graphical displays, subprocesses, network connections
        or any other environment data which should not be kept around after the
        user is no longer using the environment.
        """
        pass
