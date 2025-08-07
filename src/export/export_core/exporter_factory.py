from typing import Dict, List, Tuple, Type, Callable
import numpy as np
from onnx import numpy_helper

from ..enums import CallPosition
from ..base import LayerExporter
from ..exporters.layers.relu import ReLUExporter
from ..exporters.layers.fc import FullyConnectedExporter, QGemmExporter

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
        
        self._init_operator_registry()
    
    def _init_operator_registry(self):
        """Initialize the operator registry with handlers for each operator type"""
        self.operator_registry = {
            "Relu": {
                "exporter_class": ReLUExporter,
                "headers": ['nn_functions.h'],
                "config_handler": self._configure_default_exporter
            },
            "Gemm": {
                "exporter_class": FullyConnectedExporter,
                "headers": ['nn_functions.h'],
                "config_handler": self._configure_fc_exporter
            },
            "QGemm": {
                "exporter_class": QGemmExporter,
                "headers": ['nn_functions.h'],
                "config_handler": self._configure_qgemm_exporter
            }
        }
    
    def create_exporters(self):
        """Create exporter objects for each layer in the graph"""
        input_names = [i.name for i in self.graph.input]
        output_names = [o.name for o in self.graph.output]
        required_headers = set(self.include_list)
        initializers = {init.name: init for init in self.graph.initializer}

        for node in self.graph.node:
            if node.op_type not in self.operator_registry:
                print(f"Warning: Unsupported operator {node.op_type} in ONNX model. Skipping.")
                continue
            
            op_info = self.operator_registry[node.op_type]
            required_headers.update(op_info["headers"])
            
            exporter = self._create_base_exporter(
                node, 
                op_info["exporter_class"], 
                input_names, 
                output_names
            )
            
            op_info["config_handler"](exporter, node, initializers)
            
            self._register_exporter(exporter)
            
        return {
            'exporters': self.layer_exporters,
            'function_calls': self.function_calls,
            'defines': self.defines,
            'includes': self.include_list
        }
    
    def _create_base_exporter(self, node, ExporterClass, input_names, output_names):
        """Create a basic exporter with common parameters"""
        input_name = node.input[0]
        output_name = node.output[0]
        
        call_position = self._determine_call_position(input_name, output_name, input_names, output_names)
        
        input_idx = self.tensor_offsets.get(input_name, 0)
        output_idx = self.tensor_offsets.get(output_name, 0)
        
        try:
            input_shape = tuple(d.dim_value for d in self.value_info[input_name].type.tensor_type.shape.dim)
        except KeyError:
            print(f"Warning: Input tensor '{input_name}' not found in value_info. Using default shape.")
            input_shape = (1, 10)  # Default shape, adjust as needed
            
        try:
            output_shape = tuple(d.dim_value for d in self.value_info[output_name].type.tensor_type.shape.dim)
        except KeyError:
            print(f"Warning: Output tensor '{output_name}' not found in value_info. Using default shape.")
            output_shape = (1, 5)  # Default shape, adjust as needed


        return ExporterClass(
            name=node.name,
            input_shape=input_shape,
            output_shape=output_shape,
            input_idx=input_idx,
            output_idx=output_idx,
            datatype="int8_t",
            call_position=call_position
        )
    
    def _determine_call_position(self, input_name, output_name, input_names, output_names):
        """Determine the call position of a node"""
        is_first = input_name in input_names
        is_last = output_name in output_names
        
        if is_first and is_last:
            return CallPosition.BOTH
        elif is_first:
            return CallPosition.FIRST
        elif is_last:
            return CallPosition.LAST
        else:
            return CallPosition.BETWEEN
    
    def _configure_default_exporter(self, exporter, node, initializers):
        """Default configuration for exporters that don't need special handling"""
        # This is a no-op for simple operators like ReLU
        pass
    
    def _configure_fc_exporter(self, exporter, node, initializers):
        """Configure a fully connected exporter with weights and biases"""
        output_shape = exporter.output_shape
        
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
    
    def _configure_qgemm_exporter(self, exporter, node, initializers):
        """Configure a QGemm exporter with weights, biases, and quantization parameters"""
        output_shape = exporter.output_shape
        
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
        
        input_scale = None
        weight_scale = None
        output_scale = None
        input_zero_point = 0
        weight_zero_point = 0
        bias_zero_point = 0
        
        # Look for quantization attributes in the node
        for attr in node.attribute:
            if attr.name == 'input_scale':
                input_scale = attr.f
            elif attr.name == 'weight_scale':
                weight_scale = attr.f
            elif attr.name == 'output_scale':
                output_scale = attr.f
            elif attr.name == 'input_zero_point':
                input_zero_point = attr.i
            elif attr.name == 'weight_zero_point':
                weight_zero_point = attr.i
            elif attr.name == 'bias_zero_point':
                bias_zero_point = attr.i
        

        if input_scale is None or weight_scale is None or output_scale is None:
            input_scale = 0.1
            weight_scale = 0.1
            output_scale = 0.1
            print(f"Warning: Using default quantization scales for {node.name}. This may affect accuracy.")
        
        exporter.set_quantization_params(
            input_scale=input_scale,
            weight_scale=weight_scale,
            output_scale=output_scale,
            input_zero_point=input_zero_point,
            weight_zero_point=weight_zero_point,
            bias_zero_point=bias_zero_point
        )
    def _register_exporter(self, exporter):
        """Register an exporter and collect its artifacts"""
        self.layer_exporters.append(exporter)
        self.function_calls.append(exporter.get_function_call())
        self.defines.extend(exporter.get_defines())
        self.include_list.extend(exporter.get_include())