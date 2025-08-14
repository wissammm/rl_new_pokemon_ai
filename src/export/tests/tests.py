import sys
import os
import random
import time
import unittest
from export.exporters.parameters import ExportParameters
from quantize.quantize import FullQuantizer
import torch
import torch.nn as nn
import onnx
import onnxruntime as ort
import numpy as np
from onnx import shape_inference
from onnx import helper
from export.passes.fusion_pass import GemmQuantDequantFusionPass
from export.passes.fusion_pass import QGemmReluFusionPass
from export.passes.delete_pass import DeleteQuantizePass
import torch.nn.functional as F

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, project_root)

from src.env.core import BattleCore
import rustboyadvance_py
import src.data.parser
import src.data.pokemon_data
import jinja2

from typing import List, Any, Union

from export.onnx_exporter import ONNXExporter
from src import BIOS_PATH, MAP_PATH

def launch_makefile():
    makefile_path = os.path.join(os.path.dirname(__file__), 'gba', 'Makefile')
    if not os.path.exists(makefile_path):
        raise FileNotFoundError(f"Makefile not found at {makefile_path}")
    
    os.system(f"make -C {os.path.dirname(makefile_path)}")

def setup_stop_addr(parser, gba):
    addr_write = int(parser.get_address("stopWriteData"),16)
    addr_read = int(parser.get_address("stopReadData"),16)
    gba.add_stop_addr(addr_write,1,True, "stopWriteData",3)
    gba.add_stop_addr(addr_read,1,True, "stopReadData",4)
    return addr_write, addr_read

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
            array_data=np.array(array_data, dtype=np.int8),
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
        self.header_template_path = os.path.join(os.path.dirname(__file__), '../templates/forward_header.jinja')
        self.header_template_path = os.path.abspath(self.header_template_path)
        self.template_parameters_path = os.path.join(os.path.dirname(__file__), '../templates/parameters.jinja')
        self.template_parameters_path = os.path.abspath(self.template_parameters_path)
        self.rom_path = os.path.join(os.path.dirname(__file__), 'gba/gba.elf')
        self.map_path = os.path.join(os.path.dirname(__file__), 'gba/build/gba.map')
        
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

        ort_session = ort.InferenceSession(onnx_path)

        input_random = np.random.randint(-128, 128, (1, 10), dtype=np.int8)
        input_for_onnx = input_random.astype(np.float32)
        ort_inputs = {"input": input_for_onnx}
        ort_outs = ort_session.run(None, ort_inputs)

        exporter = ONNXExporter(onnx_path)
        exporter.export(
            output_dir=os.path.join(os.path.dirname(__file__), "gba")
        )

        launch_makefile()

        gba = rustboyadvance_py.RustGba()
        gba.load(BIOS_PATH, self.rom_path)
        parser = src.data.parser.MapAnalyzer(self.map_path)
        addr_write, addr_read = setup_stop_addr(parser, gba)

        output_addr = int(parser.get_address("output"),16)
        input_addr = int(parser.get_address("input"),16)


        id = gba.run_to_next_stop(20000)
        while id != 3:
            id = gba.run_to_next_stop(20000)
        
        gba.write_i8_list(input_addr, input_random.reshape(-1).tolist())
        print(gba.read_i8_list(input_addr, 10))
        gba.write_u16(addr_write, 0)

        id = gba.run_to_next_stop(20000)
        while id != 4:
            id = gba.run_to_next_stop(20000)
        
        output_read = gba.read_i8_list(output_addr, 10)
        onnx_output_int8 = np.clip(np.round(ort_outs[0]), -128, 127).astype(np.int8).reshape(-1)

        # Convert output_read to numpy array for comparison
        gba_output = np.array(output_read, dtype=np.int8).reshape(-1)

        print("ONNX output (int8):", onnx_output_int8)
        print("GBA output:", gba_output)
        #Compare initial input with output
        self.assertTrue(np.array_equal(onnx_output_int8, gba_output))

    def test_export_fc_forward(self):
        class SingleFC(nn.Module):
            def __init__(self):
                super(SingleFC, self).__init__()
                self.fc = nn.Linear(10, 5, bias=True)
                self.fc.weight.data = torch.randint(-5, 10, self.fc.weight.shape).float()
                self.fc.bias.data = torch.randint(-5, 12, self.fc.bias.shape).float()
            def forward(self, x):
                return self.fc(x)
        
        model = SingleFC()
        model.eval()

        dummy_input = torch.randn(1, 10)
        onnx_path = "single_fc.onnx"
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=11
        )

        ort_session = ort.InferenceSession(onnx_path)

        # Generate int8 input and run ONNX inference
        input_random = np.random.randint(-18, 12, (1, 10), dtype=np.int8)
        input_for_onnx = input_random.astype(np.float32)
        ort_inputs = {"input": input_for_onnx}
        ort_outs = ort_session.run(None, ort_inputs)

        exporter = ONNXExporter(onnx_path)
        exporter.export(
            output_dir=os.path.join(os.path.dirname(__file__), "gba")
        )

        launch_makefile()

        gba = rustboyadvance_py.RustGba()
        gba.load(BIOS_PATH, self.rom_path)
        parser = src.data.parser.MapAnalyzer(self.map_path)
        addr_write, addr_read = setup_stop_addr(parser, gba)

        output_addr = int(parser.get_address("output"), 16)
        input_addr = int(parser.get_address("input"), 16)

        id = gba.run_to_next_stop(20000)
        while id != 3:
            id = gba.run_to_next_stop(20000)

        gba.write_i8_list(input_addr, input_random.reshape(-1).tolist())
        gba.write_u16(addr_write, 0)

        id = gba.run_to_next_stop(20000)
        while id != 4:    
            id = gba.run_to_next_stop(20000)

        output_read = gba.read_i8_list(output_addr, 5)
        onnx_output_int8 = np.clip(np.round(ort_outs[0]), -128, 127).astype(np.int8).reshape(-1)
        gba_output = np.array(output_read, dtype=np.int8).reshape(-1)

        print("ONNX output (int8):", onnx_output_int8)
        print("GBA output:", gba_output)
        self.assertTrue(np.array_equal(onnx_output_int8, gba_output))

    def test_export_fc_relu_full_quantized(self):
        class FCReLU(nn.Module):
            def __init__(self):
                super().__init__()
                self.w0 = nn.Parameter(torch.randn(10, 5))
                self.b0 = nn.Parameter(torch.randn(5))
                self.w1 = nn.Parameter(torch.randn(5, 3))
                self.b1 = nn.Parameter(torch.randn(3))

            def forward(self, x):
                x = torch.matmul(x, self.w0) + self.b0
                x = F.relu(x)
                x = torch.matmul(x, self.w1) + self.b1
                x = F.relu(x)
                return x
            
        model = FCReLU()
        model.eval()
        dummy_input = torch.randn(1, 10)
        onnx_path = "fc_relu.onnx"
        quantized_onnx_path = "fc_relu_quant.onnx"


        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=13,                
            do_constant_folding=True,       
            training=torch.onnx.TrainingMode.EVAL,
        )


        quantizer = FullQuantizer(onnx_path, quantized_onnx_path)
        calib_reader = FullQuantizer.create_fake_calibration_data(onnx_path, num_samples=10)
        quantizer.quantize(calib_reader)

        quantized_model = onnx.load(quantized_onnx_path)
        inferred_model = shape_inference.infer_shapes(quantized_model)
        onnx.save(inferred_model, quantized_onnx_path)
        
        exporter = ONNXExporter(quantized_onnx_path)
        exporter.export(
            output_dir=os.path.join(os.path.dirname(__file__), "gba")
        )

        launch_makefile()

    def test_fuse_gemm_quantize_dequantize(self):
        class FCReLU(nn.Module):
            def __init__(self):
                super().__init__()
                self.w0 = nn.Parameter(torch.randn(10, 5))
                self.b0 = nn.Parameter(torch.randn(5))
                self.w1 = nn.Parameter(torch.randn(5, 3))
                self.b1 = nn.Parameter(torch.randn(3))

            def forward(self, x):
                x = torch.matmul(x, self.w0) + self.b0
                x = F.relu(x)
                x = torch.matmul(x, self.w1) + self.b1
                x = F.relu(x)
                return x
            
        model = FCReLU()
        model.eval()
        dummy_input = torch.randn(1, 10)
        onnx_path = "fc_relu.onnx"
        quantized_onnx_path = "fc_relu_quant.onnx"


        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=13,                
            do_constant_folding=True,       
            training=torch.onnx.TrainingMode.EVAL,
        )


        quantizer = FullQuantizer(onnx_path, quantized_onnx_path)
        calib_reader = FullQuantizer.create_fake_calibration_data(onnx_path, num_samples=10)
        quantizer.quantize(calib_reader)

        quantized_model = onnx.load(quantized_onnx_path)
        inferred_model = shape_inference.infer_shapes(quantized_model)

        onnx.save(inferred_model, quantized_onnx_path)
        onnx_model = onnx.load(quantized_onnx_path)
        from export.passes.fusion_pass import GemmQuantDequantFusionPass
        from export.passes.fusion_pass import QGemmReluFusionPass
        from export.passes.delete_pass import DeleteQuantizePass

        fusion_pass = GemmQuantDequantFusionPass()
        fusion_pass.run(onnx_model.graph) 
        # relu_fusion_pass = QGemmReluFusionPass()
        # relu_fusion_pass.run(onnx_model.graph)
        delete_pass = DeleteQuantizePass()
        delete_pass.run(onnx_model.graph)

        onnx.save(onnx_model, "fused_gemm_model.onnx")  
        exporter = ONNXExporter("fused_gemm_model.onnx")
        exporter.export(
            output_dir=os.path.join(os.path.dirname(__file__), "gba")
        )
        
        launch_makefile()

    def test_qgemmcustom_op(self):
        class FCQuant(nn.Module):
            def __init__(self):
                super().__init__()
                self.w0 = nn.Parameter(torch.randn(10, 5))
                self.b0 = nn.Parameter(torch.randn(5))

            def forward(self, x):
                x = torch.matmul(x, self.w0) + self.b0
                return x
            
        model = FCQuant()
        model.eval()
        dummy_input = torch.randn(1, 10)
        onnx_path = "fc.onnx"
        quantized_onnx_path = "fc_quant.onnx"


        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=13,                
            do_constant_folding=True,       
            training=torch.onnx.TrainingMode.EVAL,
        )


        quantizer = FullQuantizer(onnx_path, quantized_onnx_path)
        calib_reader = FullQuantizer.create_fake_calibration_data(onnx_path, num_samples=10)
        quantizer.quantize(calib_reader)

        quantized_model = onnx.load(quantized_onnx_path)
        inferred_model = shape_inference.infer_shapes(quantized_model)

        onnx.save(inferred_model, quantized_onnx_path)
        onnx_model = onnx.load(quantized_onnx_path)


        fusion_pass = GemmQuantDequantFusionPass()
        fusion_pass.run(onnx_model.graph) 
        # relu_fusion_pass = QGemmReluFusionPass()
        # relu_fusion_pass.run(onnx_model.graph)
        delete_pass = DeleteQuantizePass()
        delete_pass.run(onnx_model.graph)

        onnx.save(onnx_model, "fused_gemm_model.onnx")  
        exporter = ONNXExporter("fused_gemm_model.onnx")
        exporter.export(
            output_dir=os.path.join(os.path.dirname(__file__), "gba")
        )
        
        launch_makefile()
        


if __name__ == "__main__":
    unittest.main()



