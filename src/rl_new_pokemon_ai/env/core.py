import random
import sys
import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List, Set
from dataclasses import dataclass
from enum import Enum
import rich
from rich.console import Console
from rich.table import Table
import pandas as pd
import shutil
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from src import (
from rl_new_pokemon_ai import (
    ROM_PATH,
    BIOS_PATH,
    MAP_PATH,
    POKEMON_CSV_PATH,
    SAVE_PATH,
    PKMN_MOVES_PATH,
)

import rustboyadvance_py
import src.data.parser
import src.data.pokemon_data

random.seed(124)


def clear_save_path():
    """Delete all files and folders inside SAVE_PATH."""
    if os.path.exists(SAVE_PATH):
        for filename in os.listdir(SAVE_PATH):
            file_path = os.path.join(SAVE_PATH, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

class TurnType(Enum):
    """Enumeration for different turn types"""
    CREATE_TEAM = "create_team"  # Initial team creation
    GENERAL = "general"  # Both players act simultaneously
    PLAYER = "player"    # Only player acts
    ENEMY = "enemy"      # Only enemy acts
    DONE = "done"        # Battle is finished


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
            self.pending_actions = {'player': None, 'enemy': None}


class BattleCore:
    """
    Low-level battle engine interface.
    Handles GBA emulator, memory operations, and stop conditions.
    """
    
    def __init__(self, rom_path: str, bios_path: str, map_path: str, steps: int = 32000, setup: bool = True):
        
        self.rom_path = rom_path
        self.bios_path = bios_path
        self.map_path = map_path
        self.steps = steps
        # Initialize parser and GBA emulator
        self.parser = src.data.parser.MapAnalyzer(map_path)
        self.gba = rustboyadvance_py.RustGba()
        self.gba.load(bios_path, rom_path)
        
        if setup:
            self.setup_addresses()
            self.setup_stops()

    
    def setup_addresses(self):
        """Setup memory addresses from the map file"""
        self.addrs = {
            'stopHandleTurnCreateTeam': int(self.parser.get_address('stopHandleTurnCreateTeam'), 16),
            'stopHandleTurn': int(self.parser.get_address('stopHandleTurn'), 16),
            'stopHandleTurnPlayer': int(self.parser.get_address('stopHandleTurnPlayer'), 16),
            'stopHandleTurnEnemy': int(self.parser.get_address('stopHandleTurnEnemy'), 16),
            'stopHandleTurnEnd': int(self.parser.get_address('stopHandleTurnEnd'), 16),
            'monDataPlayer': int(self.parser.get_address('monDataPlayer'), 16),
            'monDataEnemy': int(self.parser.get_address('monDataEnemy'), 16),
            'playerTeam': int(self.parser.get_address('playerTeam'), 16),
            'enemyTeam': int(self.parser.get_address('enemyTeam'), 16),
            'legalMoveActionsPlayer': int(self.parser.get_address('legalMoveActionsPlayer'), 16),
            'legalMoveActionsEnemy': int(self.parser.get_address('legalMoveActionsEnemy'), 16),
            'legalSwitchActionsPlayer': int(self.parser.get_address('legalSwitchActionsPlayer'), 16),
            'legalSwitchActionsEnemy': int(self.parser.get_address('legalSwitchActionsEnemy'), 16),
            'actionDonePlayer': int(self.parser.get_address('actionDonePlayer'), 16),
            'actionDoneEnemy': int(self.parser.get_address('actionDoneEnemy'), 16),
        }
    
    def setup_stops(self):
        """Setup stop addresses for turn handling"""
        self.gba.add_stop_addr(self.addrs['stopHandleTurnCreateTeam'], 1, True, 'stopHandleTurnCreateTeam', 0)
        self.gba.add_stop_addr(self.addrs['stopHandleTurn'], 1, True, 'stopHandleTurn', 1)
        self.gba.add_stop_addr(self.addrs['stopHandleTurnPlayer'], 1, True, 'stopHandleTurnPlayer', 2)
        self.gba.add_stop_addr(self.addrs['stopHandleTurnEnemy'], 1, True, 'stopHandleTurnEnemy', 3)
        self.gba.add_stop_addr(self.addrs['stopHandleTurnEnd'], 1, True, 'stopHandleTurnEnd', 4)
        
        # Store stop IDs for different turn types
        self.stop_ids = {
            0: TurnType.CREATE_TEAM,
            1: TurnType.GENERAL,
            2: TurnType.PLAYER,
            3: TurnType.ENEMY,
            4: TurnType.DONE
        }

    def add_stop_addr(self, addr: int, size: int, read: bool, name: str, stop_id: int):
        """Add a stop address to the GBA emulator"""
        self.gba.add_stop_addr(addr, size, read, name, stop_id)
    
    def run_to_next_stop(self, max_steps = 2000000) -> int:
        """Run the emulator until we hit a stop condition"""
        stop_id = self.gba.run_to_next_stop(self.steps)
        
        # Keep running if we didn't hit a stop
        while stop_id == -1:
            max_steps -= 1
            if max_steps <= 0:
                raise TimeoutError("Reached maximum steps without hitting a stop condition")
            stop_id = self.gba.run_to_next_stop(self.steps)
        
        return stop_id
    
    def get_turn_type(self, stop_id: int) -> TurnType:
        """Convert stop ID to turn type"""
        return self.stop_ids.get(stop_id, TurnType.DONE)
    
    def read_team_data(self, agent: str) -> List[int]:
        """Read team data for specified agent"""
        if agent == 'player':
            return self.gba.read_u32_list(self.addrs['monDataPlayer'], 35 * 6)
        elif agent == 'enemy':
            return self.gba.read_u32_list(self.addrs['monDataEnemy'], 35 * 6)
        else:
            raise ValueError(f"Unknown agent: {agent}")
    
    def write_action(self, agent: str, action: int):
        """Write action for specified agent"""
        if agent == 'player':
            self.gba.write_u16(self.addrs['actionDonePlayer'], action)
        elif agent == 'enemy':
            self.gba.write_u16(self.addrs['actionDoneEnemy'], action)
        else:
            raise ValueError(f"Unknown agent: {agent}")
    
    def clear_stop_condition(self, turn_type: TurnType):
        """Clear stop condition to continue execution"""
        if turn_type == TurnType.CREATE_TEAM:
            self.gba.write_u16(self.addrs['stopHandleTurnCreateTeam'], 0)
        elif turn_type == TurnType.GENERAL:
            print("Turn = general ")
            self.gba.write_u16(self.addrs['stopHandleTurn'], 0)
        elif turn_type == TurnType.PLAYER:
            self.gba.write_u16(self.addrs['stopHandleTurnPlayer'], 0)
        elif turn_type == TurnType.ENEMY:
            self.gba.write_u16(self.addrs['stopHandleTurnEnemy'], 0)
        elif turn_type == TurnType.DONE:
            self.gba.write_u16(self.addrs['stopHandleTurnEnd'], 0)
    
    def write_team_data(self, agent: str, data: List[int]):
        """Write team data for specified agent"""
        if agent == 'player':
            self.gba.write_u32_list(self.addrs['playerTeam'], data)
        elif agent == 'enemy':
            self.gba.write_u32_list(self.addrs['enemyTeam'], data)
        else:
            raise ValueError(f"Unknown agent: {agent}")
    
    def save_savestate(self, name: str) -> str:
        """Save the current state of the emulator"""
        os.makedirs(SAVE_PATH, exist_ok=True)
        save_path = os.path.join(SAVE_PATH, f"{name}.savestate")
        self.gba.save_savestate(save_path)
        return save_path

    def load_savestate(self, name: str) -> bool:
        """Load a saved state"""
        save_path = os.path.join(SAVE_PATH, f"{name}.savestate")
        if os.path.exists(save_path):
            self.gba.load_savestate(save_path, BIOS_PATH, ROM_PATH)
            return True
        else:
            print(f"Save state {save_path} does not exist.")
            return False


class ObservationManager:
    """
    Manages extraction and formatting of observations from the battle state.
    """

    MAX_PKMN_MOVES = 4
    RAW_DATA_IDX = {
        "is_active": 0,
        "species": 1,
        "stats_begin": 2,
        "stats_end": 6,
        "moves_begin": 7,
        "moves_end": 10,
        "iv_begin": 11,
        "iv_end": 16,
        "ability": 17,
        "abitlity_2": 18,
        "specie_1": 19,
        "specie_2": 20,
        "HP": 21,
        "level": 22,
        "friendship": 23,
        "max_HP": 24,
        "held_item": 25,
        "pp_bonuses": 26,
        "personality": 27,
        "status": 28,
        "status_1": 29,
        "status_2": 30,
        "PP_begin": 31,
        "PP_end": 34,
    }

    def __init__(self, battle_core: BattleCore):
        self.battle_core = battle_core

    def get_observations(self) -> Dict[str, np.ndarray]:
        """
        For both agents, build an observation vector from raw team data.
        Steps:
          1. Extract relevant Pokémon attributes (active flag, stats, ability → status).
          2. For each move: include id, pp info, and extra move stats.
          3. Concatenate into a flat observation array for the agent.
        """
        observations = {"player": None, "enemy": None}

        # Pre-index moves_df by id for O(1) lookups
        moves_df = PkmnTeamFactory.moves_df.set_index("id").drop(columns=["moveName"])
        moves_dict = {idx: row.to_numpy() for idx, row in moves_df.iterrows()}

        for agent in observations.keys():
            # Split raw team data into 6 Pokémon entries
            raw_data_list = np.split(
                np.array(self.battle_core.read_team_data(agent), dtype=int),  # force int dtype
                indices_or_sections=6
            )
            raw_data: list[np.ndarray] = [np.array(chunk, dtype=int) for chunk in raw_data_list]  # explicit cast for mypy

            agent_data = np.array([])

            for raw_pkmn in raw_data:
                # Core Pokémon attributes
                core_data = np.concatenate([
                    [raw_pkmn[self.RAW_DATA_IDX["is_active"]]],
                    raw_pkmn[self.RAW_DATA_IDX["stats_begin"]:self.RAW_DATA_IDX["stats_end"]],
                    raw_pkmn[self.RAW_DATA_IDX["ability"]:self.RAW_DATA_IDX["status_2"]],
                ])

                # Moves data (id, pp, stats)
                moves_id = raw_pkmn[7:11]
                moves_data = np.concatenate([
                    np.concatenate([
                        [move_id],
                        [moves_dict[move_id][0]],   # max_pp from first col of stored row
                        [raw_pkmn[self.RAW_DATA_IDX["PP_begin"] + i]],
                        moves_dict[move_id][1:],    # the rest of stats
                    ])
                    for i, move_id in enumerate(moves_id) if move_id in moves_dict
                ])

                # Merge into agent array
                agent_data = np.concatenate([agent_data, core_data, moves_data])

            observations[agent] = src.data.pokemon_data.to_pandas_team_dump_data(agent_data)

        return observations
     

    def get_observation_space_size(self) -> int:
        """Get the size of the observation space (to be implemented)"""
        return None


class ActionManager:
    """
    Manages action validation and execution.
    """
    
    def __init__(self, battle_core: BattleCore):
        self.battle_core = battle_core
        self.action_space_size = 10  # Actions 0-9
    
    def is_valid_action(self, action: int) -> bool:
        """Check if action is valid (simplified version)"""
        return 0 <= action <= 9
    
    def write_actions(self, turn_type: TurnType, actions: Dict[str, int]):
        """Write actions based on turn type"""
        if turn_type == TurnType.PLAYER and 'player' in actions:
            self.battle_core.write_action('player', actions['player'])
        elif turn_type == TurnType.ENEMY and 'enemy' in actions:
            self.battle_core.write_action('enemy', actions['enemy'])
        elif turn_type == TurnType.GENERAL:
            # Handle simultaneous actions
            if 'player' in actions:
                self.battle_core.write_action('player', actions['player'])
            if 'enemy' in actions:
                self.battle_core.write_action('enemy', actions['enemy'])
    
    def get_legal_actions(self, agent: str) -> List[int]:
        if agent == 'player':
            legal_moves = self.battle_core.gba.read_u16_list(self.battle_core.addrs['legalMoveActionsPlayer'], 4)
            legal_switches = self.battle_core.gba.read_u16_list(self.battle_core.addrs['legalSwitchActionsPlayer'], 6)
        elif agent == 'enemy':
            legal_moves = self.battle_core.gba.read_u16_list(self.battle_core.addrs['legalMoveActionsEnemy'], 4)
            legal_switches = self.battle_core.gba.read_u16_list(self.battle_core.addrs['legalSwitchActionsEnemy'], 6)
        else:
            raise ValueError(f"Unknown agent: {agent}")
        
        valid_moves = [i for i, move in enumerate(legal_moves) if move]
        valid_switches = [i + 4 for i, switch in enumerate(legal_switches) if switch]  # Offset switches by 4
        
        # Combine moves and switches into a single list of legal actions
        return valid_moves + valid_switches


class TurnManager:
    """
    Manages turn logic and coordination between agents.
    """
    
    def __init__(self, battle_core: BattleCore, action_manager: ActionManager):
        self.battle_core = battle_core
        self.action_manager = action_manager
        self.state = BattleState()
    
    def process_turn(self, actions: Dict[str, int]) -> bool:
        """
        Process a turn with given actions.
        Returns True if turn was completed, False if waiting for more actions.
        """
        if self.state.current_turn == TurnType.DONE:
            return True
        
        # Check if we have all required actions
        required_agents = self._get_required_agents()
        if not all(agent in actions for agent in required_agents):
            return False
        
        # Write actions
        self.action_manager.write_actions(self.state.current_turn, actions)
        
        # Clear stop condition to continue
        self.battle_core.clear_stop_condition(self.state.current_turn)
        
        # Reset pending actions
        self.state.pending_actions = {'player': None, 'enemy': None}
        self.state.waiting_for_action = False
        
        return True
    
    def advance_to_next_turn(self) -> TurnType:
        """Advance to the next turn"""
        stop_id = self.battle_core.run_to_next_stop()
        self.state.current_turn = self.battle_core.get_turn_type(stop_id)
        self.state.waiting_for_action = True
        self.state.current_step += 1
                
        return self.state.current_turn
    
    def _get_required_agents(self) -> List[str]:
        """Get list of agents required for current turn"""
        if self.state.current_turn == TurnType.GENERAL:
            return ['player', 'enemy']
        elif self.state.current_turn == TurnType.PLAYER:
            return ['player']
        elif self.state.current_turn == TurnType.ENEMY:
            return ['enemy']
        else:
            return []
    
    def is_battle_done(self) -> bool:
        """Check if battle is finished"""
        return self.state.current_turn == TurnType.DONE
    
    def get_current_turn(self) -> TurnType:
        """Get current turn type"""
        return self.state.current_turn


class EpisodeManager:
    """
    Manages episode lifecycle and state tracking.
    """
    
    def __init__(self):
        self.episode_rewards = {'player': 0.0, 'enemy': 0.0}
        self.episode_steps = 0
        self.max_episode_steps = 1000  # Configurable
    
    def reset_episode(self):
        """Reset episode state"""
        self.episode_rewards = {'player': 0.0, 'enemy': 0.0}
        self.episode_steps = 0
    
    def update_episode(self, rewards: Dict[str, float] = None):
        """Update episode state"""
        self.episode_steps += 1
        
        if rewards:
            for agent, reward in rewards.items():
                self.episode_rewards[agent] += reward
    
    def is_episode_done(self, battle_done: bool) -> bool:
        """Check if episode should end"""
        return battle_done or self.episode_steps >= self.max_episode_steps
    
    def get_episode_info(self) -> Dict[str, Any]:
        """Get episode information"""
        return {
            'episode_rewards': self.episode_rewards.copy(),
            'episode_steps': self.episode_steps,
            'max_steps_reached': self.episode_steps >= self.max_episode_steps
        }


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

class PokemonRLCore:
    """
    Main class that coordinates all components.
    This is the primary interface for the RL environment.
    """
    
    def __init__(self, rom_path: str, bios_path: str, map_path: str, max_steps: int = 200000):
        # Initialize core components
        self.battle_core = BattleCore(rom_path, bios_path, map_path, max_steps)
        self.observation_manager = ObservationManager(self.battle_core)
        self.action_manager = ActionManager(self.battle_core)
        self.turn_manager = TurnManager(self.battle_core, self.action_manager)
        self.episode_manager = EpisodeManager()
        self.save_state_manager = SaveStateManager(self.battle_core)
        
        # Environment configuration
        self.agents = ['player', 'enemy']
        self.action_space_size = 10
    
    def reset(self, save_state: Optional[str] = "state_before_create_team") -> Dict[str, pd.DataFrame]:
        """Reset the environment"""
        # Load save state if provided
        if save_state is not None and self.save_state_manager.has_state(save_state):
            loaded = self.save_state_manager.load_state(save_state)
            if not loaded:
                raise RuntimeError(f"Failed to load save state: {save_state}")
        else:
            self.episode_manager.reset_episode()
            self.turn_manager.state = BattleState()
            turn = self.turn_manager.advance_to_next_turn()
            if turn != TurnType.CREATE_TEAM:
                raise RuntimeError("Expected to start with CREATE_TEAM turn")
        
            self.save_state_manager.save_state(save_state)

        # Reset managers
        self.episode_manager.reset_episode()
        self.turn_manager.state = BattleState()
        
        # Reset team 
        turn = self.turn_manager.advance_to_next_turn()

        if turn == TurnType.CREATE_TEAM:
            player_team = self._create_random_team(POKEMON_CSV_PATH)
            enemy_team = self._create_random_team(POKEMON_CSV_PATH)
            
            self.battle_core.write_team_data('player', player_team)
            self.battle_core.write_team_data('enemy', enemy_team)
            self.battle_core.clear_stop_condition(turn)
            
        else:
            raise RuntimeError("Expected to start with CREATE_TEAM turn")

        # Advance to first turn
        self.turn_manager.advance_to_next_turn()
        
        # Get initial observations
        return self.observation_manager.get_observations()
    
    def step(self, actions: Dict[str, int]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, float], bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            actions: Dictionary of actions for each agent
            
        Returns:
            observations: New observations for each agent
            rewards: Rewards for each agent (placeholder)
            done: Whether the episode is finished
            info: Additional information
        """
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
        rewards = {'player': 0.0, 'enemy': 0.0}
        
        # Check if episode is done
        battle_done = self.turn_manager.is_battle_done()
        episode_done = self.episode_manager.is_episode_done(battle_done)
        
        # Update episode
        self.episode_manager.update_episode(rewards)
        
        # Prepare info
        info = {
            'current_turn': self.turn_manager.get_current_turn(),
            'battle_done': battle_done,
            'episode_info': self.episode_manager.get_episode_info()
        }
        
        return observations, rewards, episode_done, info
    
    def get_current_turn_type(self) -> TurnType:
        """Get current turn type"""
        return self.turn_manager.get_current_turn()
    
    def get_required_agents(self) -> List[str]:
        """Get agents required for current turn"""
        return self.turn_manager._get_required_agents()
    
    def is_waiting_for_action(self) -> bool:
        """Check if environment is waiting for actions"""
        return self.turn_manager.state.waiting_for_action
    
    def _create_random_team(self, csv: str) -> List[int]:
        """
        Create a random team from the provided CSV file.

        Args:
            csv: Path to the CSV file containing Pokémon data

        Returns:
            List[int]: A flat list of integers representing the team in the format:
                    [id, level, move0, move1, move2, move3, ...]
        """
        df = pd.read_csv(csv)
        df = df[df['id'] != 0]
        random_species_list = df.sample(n=6)

        # Define item ranges
        item_range_1 = list(range(225, 178, -1)) 
        item_range_2 = list(range(175, 132, -1))  
        all_items = item_range_1 + item_range_2

        team = []
        for _, random_species in random_species_list.iterrows():
            moves_list = eval(random_species['moves'])
            random_moves = random.sample(moves_list, min(len(moves_list), 4))
            while len(random_moves) < 4:
                random_moves.append(0)
            hp_percent = 100
            item_id = random.choice(all_items)
            team.extend([random_species['id'], 10] + random_moves + [hp_percent, item_id])

        print(f"Created random team: {team}")
        return team
    
    def render(self, observations: Dict[str, pd.DataFrame], csv_path: str):
        """
        Render the current state of the battle using the rich library.

        Args:
            observations: Dictionary containing observation DataFrames for 'player' and 'enemy'.
            csv_path: Path to the CSV file containing Pokémon data.
        """
        # Load Pokémon data from the CSV file
        pokemon_data = pd.read_csv(csv_path)

        # Initialize the rich console
        console = Console()

        # Create a table with two columns: Player and Enemy
        table = Table(title="Battle State", show_header=True, header_style="bold magenta")
        table.add_column("Player", justify="center", style="cyan", no_wrap=True)
        table.add_column("Enemy", justify="center", style="red", no_wrap=True)

        # Helper function to get Pokémon name by ID
        def get_pokemon_name(pokemon_id):
            row = pokemon_data[pokemon_data['id'] == pokemon_id]
            return row['speciesName'].values[0] if not row.empty else "Unknown"

        # Get the current Pokémon for both player and enemy
        player_current = observations['player'][observations['player']['isActive'] == 1]
        enemy_current = observations['enemy'][observations['enemy']['isActive'] == 1]

        # Player's current Pokémon details
        player_current_details = ""
        if not player_current.empty:
            player_mon = player_current.iloc[0]
            player_name = get_pokemon_name(player_mon['id'])
            player_moves = player_mon['moves']
            player_pp = [
                player_mon['move1_pp'],
                player_mon['move2_pp'],
                player_mon['move3_pp'],
                player_mon['move4_pp'],
            ]
            # Add HP information for the active Pokémon
            player_current_details = f"[bold]{player_name}[/bold] - HP: {player_mon['current_hp']}/{player_mon['max_hp']}\n"
            for move, pp in zip(player_moves, player_pp):
                player_current_details += f"Move {move}: PP {pp}\n"

        # Enemy's current Pokémon details
        enemy_current_details = ""
        if not enemy_current.empty:
            enemy_mon = enemy_current.iloc[0]
            enemy_name = get_pokemon_name(enemy_mon['id'])
            enemy_moves = enemy_mon['moves']
            enemy_pp = [
                enemy_mon['move1_pp'],
                enemy_mon['move2_pp'],
                enemy_mon['move3_pp'],
                enemy_mon['move4_pp'],
            ]
            # Add HP information for the active Pokémon
            enemy_current_details = f"[bold]{enemy_name}[/bold] - HP: {enemy_mon['current_hp']}/{enemy_mon['max_hp']}\n"
            for move, pp in zip(enemy_moves, enemy_pp):
                enemy_current_details += f"Move {move}: PP {pp}\n"

        # Add current Pokémon details to the table
        table.add_row(player_current_details, enemy_current_details)

        # Player's team Pokémon names and HP
        player_team = observations['player'][observations['player']['isActive'] != 1]
        player_team_details = ""
        for _, mon in player_team.iterrows():
            mon_name = get_pokemon_name(mon['id'])
            player_team_details += f"{mon_name}: HP {mon['current_hp']}/{mon['max_hp']}\n"

        # Enemy's team Pokémon names and HP
        enemy_team = observations['enemy'][observations['enemy']['isActive'] != 1]
        enemy_team_details = ""
        for _, mon in enemy_team.iterrows():
            mon_name = get_pokemon_name(mon['id'])
            enemy_team_details += f"{mon_name}: HP {mon['current_hp']}/{mon['max_hp']}\n"

        # Add team details to the table
        table.add_row(player_team_details, enemy_team_details)

        # Print the table to the console
        console.print(table)


# Example usage
if __name__ == "__main__":
    # Configuration
    clear_save_path()
    # Initialize core
    rl_core = PokemonRLCore(ROM_PATH, BIOS_PATH, MAP_PATH)
    

    # Reset environment
    observations = rl_core.reset()

    # Example game loop
    for step in range(300):
        if step == 10:
            rl_core.reset()
            print("---------------------------")
            print()
            print("New save state")
            print("---------------------------")
            

        # Get current turn info
        current_turn = rl_core.get_current_turn_type()
        required_agents = rl_core.get_required_agents()
        
        print(f"Step {step}: Turn type = {current_turn}, Required agents = {required_agents}")
        
        # Generate random actions for required agents
        actions = {}
        for agent in required_agents:
            legal_actions = rl_core.action_manager.get_legal_actions(agent)
            if legal_actions:
                actions[agent] = random.choice(legal_actions)  # Choose a random legal action
            else:
                print(f"No legal actions available for {agent}")
        
        # Execute step
        observations, rewards, done, info = rl_core.step(actions)
        
        rl_core.battle_core.save_savestate(f"step_{step}")

        rl_core.render(observations, POKEMON_CSV_PATH)
        
        print(f"Rewards: {rewards}, Done: {done}")
        
        if done:
            print("Episode finished!")
            break
