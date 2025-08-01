import sys
import os
import random
import time
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, project_root)

from src.env.core import BattleCore
import rustboyadvance_py
import src.data.parser
import src.data.pokemon_data
import jinja2
import src.export.export
from typing import List, Any, Union
from src.export.export import ExportParameters

from src import ROM_PATH, BIOS_PATH, MAP_PATH

# class TestGbaFunctions(unittest.TestCase):
#     def setUp(self):
#         self.gba = rustboyadvance_py.RustGba()
#         self.parser = src.data.parser.MapAnalyzer(MAP_PATH)
#         self.gba.load(BIOS_PATH, ROM_PATH)

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.template_path = os.path.join(os.path.dirname(__file__), '../templates/parameters.jinja')
        self.template_path = os.path.abspath(self.template_path)
        self.exporter = ExportParameters(self.template_path)

    def test_export_array(self):
        array_data = [1, 2, 3, 4, 5]
        array_name = "test_array"
        output_path = "test_output.h"

        self.exporter.export_array(array_data, array_name, output_path=output_path, memory_region="")

        with open(output_path, 'r') as f:
            content = f.read()
        
        expected_content = f"const int8_t {array_name}[] = {{1, 2, 3, 4, 5}};"
        self.assertIn(expected_content, content)

        # if os.path.exists(output_path):
        #     os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
