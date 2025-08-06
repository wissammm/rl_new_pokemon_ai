import os
from typing import Optional, Dict, Type, List, Tuple
import numpy as np
import onnx
from onnx import shape_inference

from .enums import CallPosition
from .exporters.parameters import ExportParameters
from .exporters.forward import ExportForward
from .exporters.layers.relu import ReLUExporter
from .exporters.layers.fc import FullyConnectedExporter
from .base import LayerExporter

supported_operators: Dict[str, Tuple[Type[LayerExporter], List[str]]] = {
    "Relu": (ReLUExporter, ['nn_functions.h']),
    "Gemm": (FullyConnectedExporter, ['nn_functions.h']),
}

class ONNXExporter:
    """Exports ONNX models to C code for embedded platforms."""
    
    def __init__(self, onnx_path: str):
        """
        Initialize the ONNX exporter.
        
        Args:
            onnx_path: Path to the ONNX model file
        """
        self.onnx_path = onnx_path
        self.model = None
        self.graph = None
        self.value_info = {}
        self.tensor_sizes = {}
        self.tensor_offsets = {}
        self.layer_exporters = []
        self.function_calls = []
        self.defines = []
        self.total_buffer_size = 0
        self.include_list = []

    def load_and_preprocess(self):
        """Load ONNX model and perform shape inference"""
        self.model = onnx.load(self.onnx_path)
        self.model = shape_inference.infer_shapes(self.model)
        self.graph = self.model.graph
        
        self.value_info = {vi.name: vi for vi in self.graph.value_info}
        self.value_info.update({vi.name: vi for vi in self.graph.input})
        self.value_info.update({vi.name: vi for vi in self.graph.output})

    def calculate_tensor_sizes(self):
        """Calculate size in elements for each tensor"""
        self.tensor_sizes = {}
        for name, vi in self.value_info.items():
            shape = vi.type.tensor_type.shape
            size = 1
            for dim in shape.dim:
                size *= dim.dim_value
            self.tensor_sizes[name] = size

    def allocate_memory_sequentially(self):
        """Assign memory offsets for intermediate tensors"""
        self.tensor_offsets = {}
        current_offset = 0
        
        for node in self.graph.node:
            for output_name in node.output:
                if output_name not in [o.name for o in self.graph.output]:
                    self.tensor_offsets[output_name] = current_offset
                    current_offset += self.tensor_sizes[output_name]
        
        self.total_buffer_size = current_offset
    
    def allocate_memory_reused(self):
        """
        Assign memory offsets for tensors, reusing memory where possible.
        This is more efficient but more complex to implement.
        """
        #TODO : Implement memory reuse logic
        raise NotImplementedError("Memory reuse logic is not implemented yet.")

    def create_layer_exporters(self):
        """Create exporter objects for each layer in the graph"""
        input_names = [i.name for i in self.graph.input]
        output_names = [o.name for o in self.graph.output]
        required_headers = set(self.include_list)

        # Collect initializers from the graph
        initializers = {init.name: init for init in self.graph.initializer}

        for node in self.graph.node:
            if node.op_type not in supported_operators:
                RuntimeError(f"Unsupported operator: {node.op_type}")

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
                    from onnx import numpy_helper
                    weights = numpy_helper.to_array(initializers[weights_name])
                    exporter.weights = weights
                
                if len(node.input) > 2:
                    bias_name = node.input[2]
                    if bias_name in initializers:
                        from onnx import numpy_helper
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

    def generate_forward_function(self, template_path: str, header_template_path: str = None, 
                                output_dir: str = None, source_subdir: str = "source", include_subdir: str = "include"):
        """
        Generate the forward function C file and header.
        
        Args:
            template_path: Path to the Jinja template for the C implementation
            header_template_path: Path to the Jinja template for the header file
            output_dir: Directory where files should be saved
            source_subdir: Subdirectory for source files
            include_subdir: Subdirectory for header files
        """
        if output_dir is None:
            output_dir = os.path.dirname(self.onnx_path)
        
        source_dir = os.path.join(output_dir, source_subdir)
        include_dir = os.path.join(output_dir, include_subdir)
        
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(include_dir, exist_ok=True)
        
        c_output_path = os.path.join(source_dir, "forward.c")
        h_output_path = os.path.join(include_dir, "forward.h")
        
        forward_exporter = ExportForward(
            template_path=template_path,
            call_functions=self.function_calls,
            inputs=["int8_t *input"],
            outputs=["int8_t *output"],
            buffer_size=self.total_buffer_size,
            include_list=self.include_list,
            define_list=self.defines,
            data_type="int8_t",
            output_path=c_output_path
        )
        
        forward_exporter.export_forward()
        
        if header_template_path:
            forward_exporter.export_forward_header(header_template_path, h_output_path)

    def export(self, template_path: str, header_template_path: str = None, template_parameters_path: str= None,
            output_dir: str = "gba", source_subdir: str = "source", include_subdir: str = "include"):
        """
        Full export pipeline - converts ONNX model to C implementation.
        
        Args:
            template_path: Path to the Jinja template for the C implementation
            header_template_path: Path to the Jinja template for the header file
            output_dir: Directory where files should be saved
            source_subdir: Subdirectory for source files
            include_subdir: Subdirectory for header files
        """
        self.load_and_preprocess()
        self.calculate_tensor_sizes()
        self.allocate_memory_sequentially()
        self.create_layer_exporters()

        include_dir = os.path.join(output_dir, include_subdir)
        os.makedirs(include_dir, exist_ok=True)
        
        if template_parameters_path is None:
            template_parameters_path = os.path.join(os.path.dirname(__file__), "templates", "parameters.jinja")
        
        for layer_exporter in self.layer_exporters:
            layer_exporter.template_path = template_parameters_path
            layer_exporter.export_layer(include_dir)
            print(f"Exported layer {layer_exporter.name} parameters to {include_dir}")

        self.generate_forward_function(template_path, header_template_path, output_dir, source_subdir, include_subdir)