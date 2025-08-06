from typing import Dict, List, Tuple, Type
import numpy as np
from onnx import numpy_helper

from ..enums import CallPosition
from ..base import LayerExporter
from ..exporters.layers.relu import ReLUExporter
from ..exporters.layers.fc import FullyConnectedExporter

# Import this from your existing code
supported_operators = {
    "Relu": (ReLUExporter, ['nn_functions.h']),
    "Gemm": (FullyConnectedExporter, ['nn_functions.h']),
}

class ExporterFactory:
    """Creates layer exporters based on ONNX graph nodes"""
    
    def __init__(self, graph, value_info=None, tensor_offsets=None):
        self.graph = graph
        self.value_info = value_info or {}
        self.tensor_offsets = tensor_offsets or {}
        self.layer_exporters = []
        self.function_calls = []
        self.defines = []
        self.include_list = []
        
    def create_exporters(self):
        """Create exporter objects for each layer in the graph"""
        # This is the content of your create_layer_exporters method from onnx_graph.py
        input_names = [i.name for i in self.graph.input]
        output_names = [o.name for o in self.graph.output]
        required_headers = set(self.include_list)

        # Collect initializers from the graph
        initializers = {init.name: init for init in self.graph.initializer}

        for node in self.graph.node:
            if node.op_type not in supported_operators:
                print(f"Warning: Unsupported operator {node.op_type} in ONNX model. Skipping.")
                continue

            ExporterClass, headers = supported_operators[node.op_type]
            required_headers.update(headers)

            input_name = node.input[0]
            output_name = node.output[0]
            
            is_first = input_name in input_names
            is_last = output_name in output_names
            
            if is_first and is_last:
                call_position = CallPosition.BOTH
            elif is_first:
                call_position = CallPosition.FIRST
            elif is_last:
                call_position = CallPosition.LAST
            else:
                call_position = CallPosition.BETWEEN
            
            input_idx = self.tensor_offsets.get(input_name, 0)
            output_idx = self.tensor_offsets.get(output_name, 0)
            
            input_shape = tuple(d.dim_value for d in self.value_info[input_name].type.tensor_type.shape.dim)
            output_shape = tuple(d.dim_value for d in self.value_info[output_name].type.tensor_type.shape.dim)
            
            exporter = ExporterClass(
                name=node.name,
                input_shape=input_shape,
                output_shape=output_shape,
                input_idx=input_idx,
                output_idx=output_idx,
                datatype="int8_t",
                call_position=call_position
            )
            
            if ExporterClass == FullyConnectedExporter and node.op_type == "Gemm":
                weights_name = node.input[1]
                if weights_name in initializers:
                    weights = numpy_helper.to_array(initializers[weights_name])
                    exporter.weights = weights
                
                if len(node.input) > 2:
                    bias_name = node.input[2]
                    if bias_name in initializers:
                        biases = numpy_helper.to_array(initializers[bias_name])
                        exporter.biases = biases
                    else:
                        exporter.biases = np.zeros(output_shape[-1], dtype=np.int32)
                else:
                    exporter.biases = np.zeros(output_shape[-1], dtype=np.int32)

            self.include_list = list(required_headers)
            self.include_list.extend(exporter.get_include())
            self.layer_exporters.append(exporter)
            self.function_calls.append(exporter.get_function_call())
            self.defines.extend(exporter.get_defines())
            
        return {
            'exporters': self.layer_exporters,
            'function_calls': self.function_calls,
            'defines': self.defines,
            'includes': self.include_list
        }