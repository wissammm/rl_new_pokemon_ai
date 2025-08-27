from typing import Dict, List, Tuple, Type, Callable
import numpy as np
from onnx import numpy_helper

from ..enums import CallPosition
from ..base import LayerExporter
from ..exporters.layers.relu import ReLUExporter
from ..exporters.layers.fc import FullyConnectedExporter, QGemmCustomExporter

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
            "QGemmCustom": {
                "exporter_class": QGemmCustomExporter,
                "headers": ['nn_functions.h'],
                "config_handler": self._configure_qgemmcustom_exporter
            }
        }
    
    def create_exporters(self):
        """Create exporter objects for each layer in the graph"""
        input_names = [i.name for i in self.graph.input]
        output_names = [o.name for o in self.graph.output]
        required_headers = set(self.include_list)
        initializers = {init.name: init for init in self.graph.initializer}

        # Build dependency graph for topological sorting
        dependency_graph = {}
        tensor_producers = {}  # Maps tensor name to the node that produces it
        
        # Collect all nodes we can process
        processable_nodes = []
        for node in self.graph.node:
            if node.op_type in self.operator_registry:
                processable_nodes.append(node)
                # Record which node produces each tensor
                for output_tensor in node.output:
                    tensor_producers[output_tensor] = node
        
        # Build the dependency graph
        for node in processable_nodes:
            dependency_graph[node.name] = []
            for input_tensor in node.input:
                # Skip initializers (weights, biases)
                if input_tensor in initializers:
                    continue
                # If this input tensor is produced by another node, add dependency
                if input_tensor in tensor_producers:
                    producer_node = tensor_producers[input_tensor]
                    dependency_graph[node.name].append(producer_node.name)
        
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node_name):
            if node_name in temp_visited:
                raise ValueError("Cycle detected in graph")
            if node_name in visited:
                return
            
            temp_visited.add(node_name)
            for dep in dependency_graph.get(node_name, []):
                visit(dep)
            
            temp_visited.remove(node_name)
            visited.add(node_name)
            order.append(node_name)
        
        for node in processable_nodes:
            if node.name not in visited:
                visit(node.name)
        
        
        # Create exporters in topological order
        node_by_name = {node.name: node for node in processable_nodes}
        for node_name in order:
            node = node_by_name[node_name]
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
        
        if input_name in self.value_info:
            input_shape = tuple(d.dim_value for d in self.value_info[input_name].type.tensor_type.shape.dim)
        else:
            print(f"Warning: Input tensor '{input_name}' not found in value_info.")
            input_shape = None  # ou une valeur par défaut ou raise

        if output_name in self.value_info:
            output_shape = tuple(d.dim_value for d in self.value_info[output_name].type.tensor_type.shape.dim)
        else:
            print(f"Warning: Output tensor '{output_name}' not found in value_info.")
            output_shape = None  # ou valeur par défaut ou raise

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
    
    def _configure_qgemmcustom_exporter(self, exporter, node, initializers):
        """Configure a QGemm exporter with weights, biases, and quantization parameters"""
        output_shape = exporter.output_shape
        sx = 0 
        weights_name = node.input[1]
        quantized_weights_name = weights_name
        for n in self.graph.node:
            if n.op_type == "DequantizeLinear" and n.output[0] == weights_name:
                quantized_weights_name = n.input[0]
                break
        if quantized_weights_name in initializers:
            exporter.weights = numpy_helper.to_array(initializers[quantized_weights_name])
            exporter.weights = exporter.weights.transpose()
        else:
            exporter.weights = None

        if len(node.input) > 2:
            bias_name = node.input[2]
            quantized_bias_name = bias_name
            for n in self.graph.node:
                if n.op_type == "DequantizeLinear" and n.output[0] == bias_name:
                    quantized_bias_name = n.input[0]
                    # get the input scale factor 
                    input_scale_name = n.input[1]
                    break
            if quantized_bias_name in initializers:
                exporter.biases = numpy_helper.to_array(initializers[quantized_bias_name])
            else:
                exporter.biases = np.zeros(output_shape[-1], dtype=np.int32)
            if input_scale_name in initializers:
                input_scale = numpy_helper.to_array(initializers[input_scale_name]).item(0)
            else : 
                input_scale = 1
        else:
            exporter.biases = np.zeros(output_shape[-1], dtype=np.int32)
            input_scale = 1

        output_scale_name = node.input[3]
        output_scale =  numpy_helper.to_array(initializers[output_scale_name]).item(0)
        
        exporter.set_quantization_params(
            input_scale=input_scale,
            output_scale=output_scale
        )

    def _register_exporter(self, exporter):
        """Register an exporter and collect its artifacts"""
        self.layer_exporters.append(exporter)
        self.function_calls.append(exporter.get_function_call())
        self.defines.extend(exporter.get_defines())
        self.include_list.extend(exporter.get_include())
    
    def _get_quantized_input(self, node, graph):
        """
        If node.input[0] is the output of a DequantizeLinear node,
        return the quantized input tensor name (dequant_node.input[0]).
        Otherwise, return node.input[0].
        """
        input_name = node.input[0]
        for n in graph.node:
            if n.op_type == "DequantizeLinear" and n.output[0] == input_name:
                return n.input[0]
        return input_name