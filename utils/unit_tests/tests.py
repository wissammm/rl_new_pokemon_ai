import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import PokemonRLCore, TurnType
import rustboyadvance_py
import utils.parser
import utils.pokemon_data

MAIN_STEPS = 64000
ROM_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.elf"
BIOS_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/rustboyadvance-ng-for-rl/gba_bios.bin"
MAP_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.map"
POKEMON_CSV_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/data/csv_data/pokemon_data.csv"

class TestPokemonRLCore(unittest.TestCase):
    def setUp(self):
        self.core =  PokemonRLCore(ROM_PATH, BIOS_PATH, MAP_PATH)

    def test_advance_to_next_turn(self):
        # self.core.reset()
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

    def test_create_team(self):
                                  #id level move0 move1 move2 move3
        player_team = [164, 10, 214, 38, 203, 36,
                                    95, 10, 103, 203, 214, 38, 
                                    47, 10, 210, 164, 78, 214, 
                                    59, 10, 245, 207, 34, 129, 
                                    43, 10, 80, 230, 207, 14,
                                    367, 10, 223, 164, 102, 8]
                                    
        enemy_team = [326, 10, 207, 173, 102, 210,
                                     200, 10, 173, 195, 111, 212, 
                                     147, 10, 214, 43, 173, 86,
                                       366, 10, 8, 227, 214, 210, 
                                       135, 10, 86, 39, 42, 24, 
                                       211, 10, 40, 86, 42, 33]
        
        
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.CREATE_TEAM)

        self.core.battle_core.write_team_data('player', player_team)
        self.core.battle_core.write_team_data('enemy', enemy_team)

        addr_player = int(self.core.battle_core.parser.get_address('playerTeam'), 16)
        read_player_team = self.core.battle_core.gba.read_u32_list(addr_player, 36)

        addr_enemy = int(self.core.battle_core.parser.get_address('playerTeam'), 16)
        read_enemy_team = self.core.battle_core.gba.read_u32_list(addr_enemy, 36)

        #compare buffer read from gba with player_team
        for i in range(6):
            start = i * 6
            self.assertEqual(read_player_team[start], player_team[start])
            self.assertEqual(read_player_team[start + 1], player_team[start + 1])
            self.assertEqual(read_player_team[start + 2:start + 6], player_team[start + 2:start + 6])


        self.core.battle_core.clear_stop_condition(turn)
        turn = self.core.turn_manager.advance_to_next_turn()
        self.assertEqual(turn, TurnType.GENERAL)

        player_team_dump_data = self.core.battle_core.read_team_data('player')
        enemy_team_dump_data = self.core.battle_core.read_team_data('enemy')

        playerdf = utils.pokemon_data.to_pandas_team_dump_data(player_team_dump_data)
        enemydf = utils.pokemon_data.to_pandas_team_dump_data(enemy_team_dump_data)
        
        for i in range(6):
            start = i * 6
            self.assertEqual(playerdf.iloc[i]['id'], player_team[start])
            self.assertEqual(playerdf.iloc[i]['level'], player_team[start + 1])
            self.assertEqual(playerdf.iloc[i]['moves'], player_team[start + 2:start + 6])

        # Compare enemy team
        for i in range(6):
            start = i * 6
            self.assertEqual(enemydf.iloc[i]['id'], enemy_team[start])
            self.assertEqual(enemydf.iloc[i]['level'], enemy_team[start + 1])
            self.assertEqual(enemydf.iloc[i]['moves'], enemy_team[start + 2:start + 6])

    
    def test_use_move(self):
        pass

    def test_switch_pokemon(self):
        pass

    def test_switch_pokemon_when_one_fainted(self):
        pass

    def test_player_lost(self):
        pass

class TestGbaFunctions(unittest.TestCase):
    def setUp(self):
        self.gba = rustboyadvance_py.RustGba()
        self.parser = utils.parser.MapAnalyzer(MAP_PATH)
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
        data = [1, 2, 3, 4, 5, 6]
        self.gba.write_u32_list(addr, data)
        result = self.gba.read_u32_list(addr, len(data))
        self.assertEqual(result, data)


if __name__ == "__main__":
    unittest.main()