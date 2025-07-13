import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import PokemonRLCore
import rustboyadvance_py
import utils.parser
import utils.pokemon_data

ROM_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.elf"
BIOS_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/rustboyadvance-ng-for-rl/gba_bios.bin"
MAP_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.map"
POKEMON_CSV_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/data/csv_data/pokemon_data.csv"

class TestPokemonRLCore(unittest.TestCase):
    def setUp(self):
        self.parser = utils.parser.MapAnalyzer(MAP_PATH)
        self.gba = rustboyadvance_py.RustGba()
        self.gba.load(BIOS_PATH, ROM_PATH)
        self.core =  PokemonRLCore(ROM_PATH, BIOS_PATH, MAP_PATH)
    
    def test_read_u32(self):
        pass

    def test_read_u32_list(self):
        pass

    def test_write_u32(self):
        pass

    def test_write_u32_list(self):
        pass

    def test_create_team(self):
        pass
    
    def test_use_move(self):
        pass

    def test_switch_pokemon(self):
        pass

    def test_switch_pokemon_when_one_fainted(self):
        pass

    def test_player_lost(self):
        pass

