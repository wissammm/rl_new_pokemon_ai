import sys
import os
import random
import time
import unittest
from src.env.core import BattleCore
import rustboyadvance_py
import src.data.parser
import src.data.pokemon_data

from src import ROM_PATH, BIOS_PATH, MAP_PATH

class TestGbaFunctions(unittest.TestCase):
    def setUp(self):
        self.gba = rustboyadvance_py.RustGba()
        self.parser = src.data.parser.MapAnalyzer(MAP_PATH)
        self.gba.load(BIOS_PATH, ROM_PATH)

if __name__ == "__main__":
    unittest.main()