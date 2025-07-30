import sys
import os
import random
import time
import unittest
from src.env.core import BattleCore
import rustboyadvance_py
import src.data.parser
import src.data.pokemon_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROM_PATH = os.path.join(BASE_DIR, "../../pokeemerald_ai_rl/pokeemerald_modern.elf")
BIOS_PATH = os.path.join(BASE_DIR, "../../rustboyadvance-ng-for-rl/gba_bios.bin")
MAP_PATH = os.path.join(BASE_DIR, "../../pokeemerald_ai_rl/pokeemerald_modern.map")

class TestGbaFunctions(unittest.TestCase):
    def setUp(self):
        self.gba = rustboyadvance_py.RustGba()
        self.parser = src.data.parser.MapAnalyzer(MAP_PATH)
        self.gba.load(BIOS_PATH, ROM_PATH)

if __name__ == "__main__":
    unittest.main()