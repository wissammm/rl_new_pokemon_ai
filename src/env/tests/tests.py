import random
import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.env.core import PokemonRLCore, TurnType
import rustboyadvance_py
import src.data.parser
import src.data.pokemon_data

from src import ROM_PATH, BIOS_PATH, MAP_PATH, POKEMON_CSV_PATH, SAVE_PATH

MAIN_STEPS = 64000


class TestPokemonRLCore(unittest.TestCase):
    def setUp(self):
        self.core =  PokemonRLCore(ROM_PATH, BIOS_PATH, MAP_PATH)

    def test_advance_to_next_turn(self):
        # self.core.reset()
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

    def test_create_team(self):
        player_team = self.core._create_random_team(POKEMON_CSV_PATH)
                                    
        enemy_team = self.core._create_random_team(POKEMON_CSV_PATH)

        
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

        self.core.battle_core.write_team_data('player', player_team)
        self.core.battle_core.write_team_data('enemy', enemy_team)

        addr_player = int(self.core.battle_core.parser.get_address('playerTeam'), 16)
        read_player_team = self.core.battle_core.gba.read_u32_list(addr_player, 8*6)
        print(player_team)
        print(read_player_team)
        # self.assertEqual(read_player_team, player_team, "Player team data mismatch")

        addr_enemy = int(self.core.battle_core.parser.get_address('enemyTeam'), 16)
        read_enemy_team = self.core.battle_core.gba.read_u32_list(addr_enemy, 8*6)

        #compare buffer read from gba with player_team
        for i in range(6):
            start = i * 8
            self.assertEqual(read_player_team[start], player_team[start], "Player team ID mismatch at pokemon {i}")
            self.assertEqual(read_player_team[start + 1], player_team[start + 1], "Player team level mismatch at pokemon {i}")
            self.assertEqual(read_player_team[start + 2:start + 6], player_team[start + 2:start + 6], "Player team moves mismatch at pokemon {i}")
            self.assertEqual(read_player_team[start + 7], player_team[start + 7],f"Player team item mismatch at pokemon {i}")


        self.core.battle_core.clear_stop_condition(turn)
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)

        player_team_dump_data = self.core.battle_core.read_team_data('player')
        enemy_team_dump_data = self.core.battle_core.read_team_data('enemy')

        playerdf = utils.pokemon_data.to_pandas_team_dump_data(player_team_dump_data)
        enemydf = utils.pokemon_data.to_pandas_team_dump_data(enemy_team_dump_data)

        for i in range(6):
            start = i * 8
            self.assertEqual(playerdf.iloc[i]['id'], player_team[start],f"Player team ID mismatch at pokemon {i}")
            self.assertEqual(playerdf.iloc[i]['level'], player_team[start + 1],f"Player team level mismatch at pokemon {i}")
            self.assertEqual(playerdf.iloc[i]['moves'], player_team[start + 2:start + 6],f"Player team moves mismatch at pokemon {i}")
            self.assertEqual(playerdf.iloc[i]['held_item'], player_team[start + 7],f"Player team item mismatch at pokemon {i}")

        for i in range(6):
            start = i * 8
            self.assertEqual(enemydf.iloc[i]['id'], enemy_team[start],f"Enemy team ID mismatch at pokemon {i}")
            self.assertEqual(enemydf.iloc[i]['level'], enemy_team[start + 1],f"Enemy team level mismatch at pokemon {i}") 
            self.assertEqual(enemydf.iloc[i]['moves'], enemy_team[start + 2:start + 6],f"Enemy team moves mismatch at pokemon {i}")
            self.assertEqual(enemydf.iloc[i]['held_item'], enemy_team[start + 7],f"Enemy team item mismatch at pokemon {i}")

    
    def test_enemy_lost(self):
        # pokachu lvl 99 using shock wave (86) with 100% accyracy
        player_team = [
            25, 99, 84, 84, 84, 84, 100,0,# Pikachu with moves and 100% HP
            0, 10, 0, 0, 0, 0, 0, 0,       # Empty slots
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0
        ]
        enemy_team = [
            7, 10, 45, 45, 45, 45, 10, 0, # Squirtle use move 150 wich does nothing 10% HP
            0, 10, 0, 0, 0, 0, 0, 0,       # Empty slots
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0
        ]

        # This test case Squirtle have 100% chance to death
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

        self.core.battle_core.write_team_data('player', player_team)
        self.core.battle_core.write_team_data('enemy', enemy_team)

        self.core.battle_core.clear_stop_condition(turn)
        # Advance to the first turn
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)

        # Perform a move (e.g., player uses the first move)
        player_action = 0
        enemy_action = 0
        actions = {
            'player': player_action,
            'enemy': enemy_action
        }

        self.core.action_manager.write_actions(turn,actions)
        self.core.battle_core.clear_stop_condition(turn)

        turn = self.core.turn_manager.advance_to_next_turn()
        enemy_team_dump_data = self.core.battle_core.read_team_data('enemy')
        enemydf = utils.pokemon_data.to_pandas_team_dump_data(enemy_team_dump_data)
        #Print Hp of enemy POkemon active
        active_enemy = enemydf[enemydf['isActive'] == 1]
        enemy_updated_hp = active_enemy.iloc[0]['current_hp']
        print(f"Enemy updated HP: {enemy_updated_hp}")

        self.assertEqual(turn, TurnType.DONE)
        # self.assertLess(enemy_updated_hp, enemy_initial_hp, "Enemy HP should decrease after a move is used.")

    def test_switch_pokemon(self):
        player_team = [
            25, 1, 150, 150, 150, 150, 100, 0, # Pikachu  use move 150 wich does nothing
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0
        ]
        enemy_team = [
            7, 99, 74, 53, 54, 55, 10, 0,  # Squirtle use move 74 wich does nothing 10% HP
            8, 99, 4, 5, 9, 23, 11, 0,
            12, 99, 4, 5, 9, 23, 11, 0,
            12, 10, 0, 0, 0, 0, 10, 0,
            12, 10, 0, 0, 0, 0, 10, 0,
            12, 10, 0, 0, 0, 0, 10, 0
        ]

        # This test case Squirtle have 100% chance to death
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

        self.core.battle_core.write_team_data('player', player_team)
        self.core.battle_core.write_team_data('enemy', enemy_team)

        self.core.battle_core.clear_stop_condition(turn)
        # Advance to the first turn
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)

        player_action = 0
        enemy_action = 5
        actions = {
            'player': player_action,
            'enemy': enemy_action
        }

        self.core.action_manager.write_actions(turn,actions)
        self.core.battle_core.clear_stop_condition(turn)
        turn = self.core.turn_manager.advance_to_next_turn()

        player_team_dump_data = self.core.battle_core.read_team_data('player')
        enemy_team_dump_data = self.core.battle_core.read_team_data('enemy')
        self.assertEqual(turn, TurnType.GENERAL)

        playerdf = utils.pokemon_data.to_pandas_team_dump_data(player_team_dump_data)
        enemydf = utils.pokemon_data.to_pandas_team_dump_data(enemy_team_dump_data)
        active_enemy = enemydf[enemydf['isActive'] == 1]
        print(enemydf)
        self.assertEqual(len(active_enemy), 1, "There should be exactly one active Pokémon in the enemy team.")
        self.assertEqual(active_enemy.iloc[0]['id'], 8, "The active Pokémon in the enemy team should have ID 8.")

    def test_switch_pokemon_when_one_fainted_enemy(self):
        player_team = [
            25, 99, 84, 84, 84, 84, 100, 0,# Pikachu with moves and 100% HP
            0, 10, 0, 0, 0, 0, 0,0,        # Empty slots
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0, 0
        ]
        enemy_team = [
            7, 10, 45, 45, 45, 45, 10,0,  # Squirtle use move 150 wich does nothing 10% HP
            11, 10, 8, 3, 4, 2, 100,  0,      # Empty slots
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0
        ]

        # This test case Squirtle have 100% chance to death
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

        self.core.battle_core.write_team_data('player', player_team)
        self.core.battle_core.write_team_data('enemy', enemy_team)

        self.core.battle_core.clear_stop_condition(turn)
        # Advance to the first turn
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)

        # Perform a move (e.g., player uses the first move)
        player_action = 0
        enemy_action = 0
        actions = {
            'player': player_action,
            'enemy': enemy_action
        }

        self.core.action_manager.write_actions(turn,actions)
        self.core.battle_core.clear_stop_condition(turn)

        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.ENEMY)
        enemy_action = 5 # Switch with the [1] mon 
        actions = {
            'enemy': enemy_action
        }
        self.core.action_manager.write_actions(turn, actions)
        self.core.battle_core.clear_stop_condition(turn)
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)
        player_team_dump_data = self.core.battle_core.read_team_data('player')
        enemy_team_dump_data = self.core.battle_core.read_team_data('enemy')
        playerdf = utils.pokemon_data.to_pandas_team_dump_data(player_team_dump_data)
        enemydf = utils.pokemon_data.to_pandas_team_dump_data(enemy_team_dump_data)
        active_enemy = enemydf[enemydf['isActive'] == 1]
        self.assertEqual(len(active_enemy), 1, "There should be exactly one active Pokémon in the enemy team.")
        self.assertEqual(active_enemy.iloc[0]['id'], 11, "The active Pokémon in the enemy team should have ID 11.")

    def test_switch_pokemon_when_one_fainted_player(self):
        player_team = [
            7, 2, 45, 45, 45, 45, 10, 0,
            26, 10, 8, 3, 4, 2, 100,  0,    
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0
        ]
        enemy_team = [
             25, 10, 84, 84, 84, 84, 100,0,  # Pikachu with moves and 100% HP
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0,
            0, 10, 0, 0, 0, 0, 0,0
        ]

        # This test case Pikachu has 100% chance to faint
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

        self.core.battle_core.write_team_data('player', player_team)
        self.core.battle_core.write_team_data('enemy', enemy_team)

        self.core.battle_core.clear_stop_condition(turn)
        # Advance to the first turn
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)

        # Both use first move (Pikachu will faint)
        player_action = 0
        enemy_action = 0
        actions = {
            'player': player_action,
            'enemy': enemy_action
        }

        self.core.action_manager.write_actions(turn, actions)
        self.core.battle_core.clear_stop_condition(turn)

        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.PLAYER)
        player_action = 5  # Switch with the [1] mon (Bulbasaur)
        actions = {
            'player': player_action
        }
        self.core.action_manager.write_actions(turn, actions)
        self.core.battle_core.clear_stop_condition(turn)
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)
        player_team_dump_data = self.core.battle_core.read_team_data('player')
        enemy_team_dump_data = self.core.battle_core.read_team_data('enemy')
        playerdf = utils.pokemon_data.to_pandas_team_dump_data(player_team_dump_data)
        enemydf = utils.pokemon_data.to_pandas_team_dump_data(enemy_team_dump_data)
        active_player = playerdf[playerdf['isActive'] == 1]
        self.assertEqual(len(active_player), 1, "There should be exactly one active Pokémon in the player team.")
        self.assertEqual(active_player.iloc[0]['id'], 26, "The active Pokémon in the player team should have ID 26.")
    
    # def test_special_moves(): 
    #     #ROAR FLEE FLY MULTIMOVE MULTIHIT ENCORE move 5 also 
    #     pass
    # def test_status():
    #     pass

    # def test_all_moves():
    #     # # Test all moves
    #     pass




class TestGbaFunctions(unittest.TestCase):
    def setUp(self):
        self.gba = rustboyadvance_py.RustGba()
        self.parser = src.data.parser.MapAnalyzer(MAP_PATH)
        self.gba.load(BIOS_PATH, ROM_PATH)
    
    def test_read_u32(self):
        self.gba.add_stop_addr(int(self.parser.get_address('stopTestReadWrite'),16), 1, True, "stopTestReadWrite", 12)
        addr = int(self.parser.get_address('testBuffer'), 16)

        id = self.gba.run_to_next_stop(MAIN_STEPS)
        while id != 12 :
            id = self.gba.run_to_next_stop(MAIN_STEPS)
        result = self.gba.read_u32(addr)
        # Check if the result equlas 3 
        self.assertEqual(result, 3)

    def test_read_u32_list(self):
        self.gba.add_stop_addr(int(self.parser.get_address('stopTestReadWrite'), 16), 1, True, "stopTestReadWrite", 12)
        addr = int(self.parser.get_address('listTestBuffer'), 16)
        id = self.gba.run_to_next_stop(MAIN_STEPS)
        while id != 12:
            id = self.gba.run_to_next_stop(MAIN_STEPS)
        
        result = self.gba.read_u32_list(addr, 6)
        expected = [10, 87, 76, 65, 1, 0]
        
        self.assertEqual(result, expected)

    def test_write_u32(self):
        self.gba.add_stop_addr(int(self.parser.get_address('stopTestReadWrite'), 16), 1, True, "stopTestReadWrite", 12)
        addr = int(self.parser.get_address('testBuffer'), 16)
        id = self.gba.run_to_next_stop(MAIN_STEPS)
        while id != 12:
            id = self.gba.run_to_next_stop(MAIN_STEPS)
        self.gba.write_u32(addr, 42)
        result = self.gba.read_u32(addr)
        self.assertEqual(result, 42)

    def test_write_u32_list(self):
        self.gba.add_stop_addr(int(self.parser.get_address('stopTestReadWrite'), 16), 1, True, "stopTestReadWrite", 12)
        addr = int(self.parser.get_address('listTestBuffer'), 16)
        id = self.gba.run_to_next_stop(MAIN_STEPS)
        while id != 12:
            id = self.gba.run_to_next_stop(MAIN_STEPS)
        data = [random.randint(0, 300) for _ in range(42)]
    
        self.gba.write_u32_list(addr, data)
        result = self.gba.read_u32_list(addr, len(data))
        self.assertEqual(result, data)

    def test_save_load_state(self):
        self.gba.add_stop_addr(int(self.parser.get_address('stopTestReadWrite'), 16), 1, True, "stopTestReadWrite", 12)
        addr = int(self.parser.get_address('listTestBuffer'), 16)
        id = self.gba.run_to_next_stop(MAIN_STEPS)
        while id != 12:
            id = self.gba.run_to_next_stop(MAIN_STEPS)
        data = [random.randint(0, 300) for _ in range(42)]
    
        self.gba.write_u32_list(addr, data)
        
        # Save the state
        self.gba.save_savestate("test_state.sav")
        
        # Load the state
        self.gba.load_savestate("test_state.sav",BIOS_PATH, ROM_PATH)
        
        result = self.gba.read_u32_list(addr, len(data))
        self.assertEqual(result, data)
        


if __name__ == "__main__":
    unittest.main()