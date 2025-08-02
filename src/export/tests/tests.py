import sys
import os
import random
import time
import unittest
import torch
import torch.nn as nn
import onnx


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
from src.export.export import ExportForward
from src.export.onnx_graph import ONNXExporter
from src import ROM_PATH, BIOS_PATH, MAP_PATH

# class TestGbaFunctions(unittest.TestCase):
#     def setUp(self):
#         self.gba = rustboyadvance_py.RustGba()
#         self.parser = src.data.parser.MapAnalyzer(MAP_PATH)
#         self.gba.load(BIOS_PATH, ROM_PATH)

class TestExportParameters(unittest.TestCase):
    def setUp(self):
        self.template_path = os.path.join(os.path.dirname(__file__), '../templates/parameters.jinja')
        self.template_path = os.path.abspath(self.template_path)

    def test_export_array(self):
        array_data = [1, 2, 3, 4, 5]
        array_name = "test_array"
        output_path = "test_output.h"
        memory_region = "const"
        datatype = "int8_t"

        exporter = ExportParameters(
            template_path=self.template_path,
            array_data=array_data,
            array_name=array_name,
            memory_region=memory_region,
            datatype=datatype,
            output_path=output_path
        )
        exporter.export_array()

        with open(output_path, 'r') as f:
            content = f.read()
        
        expected_content = f"{memory_region} {datatype} {array_name}[] = {{1, 2, 3, 4, 5}};"
        self.assertIn(expected_content, content)

        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)

class TestExportForward(unittest.TestCase):
    def setUp(self):
        self.template_path = os.path.join(os.path.dirname(__file__), '../templates/forward.jinja')
        self.template_path = os.path.abspath(self.template_path)
        
    def test_export_forward_three_relu(self):
        class ThreeReLUOnly(nn.Module):
            def __init__(self):
                super(ThreeReLUOnly, self).__init__()
                self.relu1 = nn.ReLU()
                self.relu2 = nn.ReLU()
                self.relu3 = nn.ReLU()

            def forward(self, x):
                x = self.relu1(x)
                x = self.relu2(x)
                x = self.relu3(x)
                return x
            
        model = ThreeReLUOnly()

        model.eval()
        dummy_input = torch.randn(1, 10)

        onnx_path = "three_relu_only.onnx"
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=11
        )

        # Load the ONNX model into a variable
        onnx_model = onnx.load(onnx_path)
        exporter = ONNXExporter(onnx_path)
        exporter.export(template_path=self.template_path, output_path="forward.c")


if __name__ == "__main__":
    unittest.main()
