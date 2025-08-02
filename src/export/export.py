import os
import jinja2
from typing import Dict, Any, List, Optional, Union
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum

class CallPosition(Enum):
    FIRST = "first"  # first_node
    LAST = "last"  # last_node
    BETWEEN = "between"
    BOTH = "both" # first and last ndoe


class Exporter:
    def __init__(self, template_path: str):
        """
        Initialize with the path to a Jinja template.
        
        Args:
            template_path: Path to the Jinja template file
        """
        self.template_path = template_path
        self.template_dir = os.path.dirname(template_path)
        self.template_name = os.path.basename(template_path)
        
        # Set up Jinja environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        self.template = self.env.get_template(self.template_name)

class LayerExporter(ABC):
    """Abstract base class for layer exporters."""
    
    @abstractmethod
    def export_layer(self, output_dir: str) -> Dict[str, str]:
        """Export layer and return generated files info."""
        pass
    
    @abstractmethod
    def get_function_call(self) -> str:
        """Get the C function call for this layer."""
        pass

class ExportParameters(Exporter):
    def __init__(self, template_path: str,
                    array_data: Union[List[Any], str],
                    array_name: str,
                    memory_region: str = "", 
                    datatype: str = "int8_t",
                    output_path: str = "array_names.h"):
        """        
        Initialize with the path to a Jinja template and parameters for exporting an array.
        
        Args:
            template_path: Path to the Jinja template file
            array_data: The data for the array (either a list or formatted string)
            array_name: Name of the array variable
            memory_region: Memory region specifier (e.g., "const", "static")
            datatype: C data type (e.g., "int", "float")
            output_path: Path where the header file will be written
        """
        super().__init__(template_path)
        self.array_data = array_data
        self.array_name = array_name
        self.memory_region = memory_region
        self.datatype = datatype
        self.output_path = output_path

    def export_array(self) -> None:
        """
        Export an array to a C header file using the template.
        """

        if isinstance(self.array_data, list):
            formatted_data = "{" + ", ".join(str(item) for item in self.array_data) + "}"
        else:
            formatted_data = self.array_data
            
        params = {
            "memory_region": self.memory_region,
            "datatype": self.datatype,
            "array_name": self.array_name,
            "data": formatted_data
        }
        
        output_content = self.template.render(**params)
        
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(self.output_path, 'w') as f:
            f.write(output_content)

class ExportForward(Exporter):
    def __init__(self, template_path: str,
                 call_functions: List,
                 inputs: List,
                 outputs: List,
                 buffer_size: int,
                 include_list:List,
                 define_list: List,
                 data_type: str = "int8_t",
                 output_path: str = "forward.c"):
        """
        Initialize with the path to a Jinja template and function calls.
        
        Args:
            template_path: Path to the Jinja template file
            callFunction: List of function calls to be included in the forward function
            inputs: List of input variables for the forward function
            outputs: List of output variables for the forward function
            buffer_size: Size of the memory buffer to be used in the forward function
            include_list: List of include statements to be added at the top of the file
            define_list: List of define statements to be added at the top of the file
            data_type: C data type for the memory buffer (default is "int8_t")
            output_path: Path where the C source file will be written (default is "forward.c")
        """
        super().__init__(template_path)
        self.call_functions = call_functions
        self.inputs = inputs
        self.outputs = outputs
        self.buffer_size = buffer_size
        self.include_list = include_list
        self.define_list = define_list
        self.data_type = data_type
        self.output_path = output_path
        
    def export_forward(self, output_path: Optional[str] = None) -> None:
            """
            Export the forward function to a C source file using the template.
            Args:
                output_path: Path where the C source file will be written (optional, uses self.output_path if None)
            """
            if output_path is None:
                output_path = self.output_path
                
            params = {
                "include_list": "\n".join(f"#include {inc}" for inc in self.include_list),
                "define_list": "\n".join(f"#define {define}" for define in self.define_list),
                "data_type": self.data_type,
                "buffer_size": self.buffer_size,
                "inputs": ", ".join(self.inputs),
                "outputs": ", ".join(self.outputs),
                "call_functions": "\n    ".join(self.call_functions)
            }
            
            # Render the template
            output_content = self.template.render(**params)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Write the output file
            with open(output_path, 'w') as f:
                f.write(output_content)
            
            print(f"Forward function exported to: {output_path}")



# -------------------------------------------------- #
#                             LAYERS                                            #
# -------------------------------------------------- #

class ReLUExporter(LayerExporter):
    def __init__(self, name: str, input_shape: tuple, output_shape: tuple, input_idx: int=0, output_idx: int=0, datatype : str = "int8_t", call_position: CallPosition = CallPosition.BETWEEN):
        self.name = name.replace("/", "_").upper()
        self.input_shape = input_shape
        self.output_shape = output_shape
        self.input_idx = input_idx
        self.output_idx = output_idx
        self.datatype = datatype
        self.call_position = call_position
        
    def get_function_call(self) -> str:
        if self.call_position == CallPosition.FIRST:
            return f"relu_{self.datatype}(input, mem_buffer + {self.name.upper()}_OUTPUT_IDX,{self.name.upper()}_SIZE);"
        elif self.call_position == CallPosition.LAST:
            return f"relu_{self.datatype}(mem_buffer + {self.name.upper()}_INPUT_IDX, output,{self.name.upper()}_SIZE);"
        elif self.call_position == CallPosition.BETWEEN:
            return f"relu_{self.datatype}(mem_buffer + {self.name.upper()}_INPUT_IDX, mem_buffer + {self.name.upper()}_OUTPUT_IDX,{self.name.upper()}_SIZE);"
        elif self.call_position == CallPosition.BOTH:
            return f"relu_{self.datatype}(input, output);"
        else:
            raise ValueError("Invalid call position specified.")
    
    def export_layer(self, output_dir: str) -> Dict[str, str]:
        """Export ReLU layer implementation."""
        files_generated = {}

    def get_defines(self) -> List[str]:
        """Get the list of defines for the ReLU layer."""
        return [
            f" {self.name.upper()}_INPUT_IDX {self.input_idx}",
            f" {self.name.upper()}_OUTPUT_IDX {self.output_idx}",
            f" {self.name.upper()}_SIZE {self.input_shape[1]}",
        ]
    

# class FullyConnectedExporter(Exporter, LayerExporter):
#     def __init__(self, 
#                  template_path: str,
#                  name: str,
#                  inputs: np.ndarray, 
#                  outputs: np.ndarray, 
#                  weights: np.ndarray, 
#                  biases: np.ndarray,
#                  order: int,
#                  input_idx: int = 0,
#                  output_idx: int = 0,
#                  data_type: str = "int8_t"):
    
#         super().__init__(template_path)
#         self.name = name
#         self.inputs = inputs
#         self.outputs = outputs
#         self.weights = weights
#         self.biases = biases
#         self.input_shape = inputs.shape
#         self.output_shape = outputs.shape
#         self.weight_shape = weights.shape
#         self.bias_shape = biases.shape
#         self.order = order
#         self.input_idx = input_idx
#         self.output_idx = output_idx
#         self.data_type = data_type
    
#     def export_layer(self, output_dir: str) -> Dict[str, str]:
#         """Export FC layer implementation and parameters."""
#         files_generated = {}
        
#         # Export weights
#         weight_exporter = ExportParameters(
#             template_path=os.path.join("templates", "array_template.h.jinja"),
#             array_data=self.weights.flatten().tolist(),
#             array_name=f"{self.name}_weights",
#             datatype=self.data_type,
#             output_path=os.path.join(output_dir, f"{self.name}_weights.h")
#         )
#         weight_exporter.export_array()
#         files_generated[f"{self.name}_weights.h"] = "weights"
        
#         # Export biases
#         bias_exporter = ExportParameters(
#             template_path=os.path.join("templates", "array_template.h.jinja"),
#             array_data=self.biases.tolist(),
#             array_name=f"{self.name}_biases",
#             datatype=self.data_type,
#             output_path=os.path.join(output_dir, f"{self.name}_biases.h")
#         )
#         bias_exporter.export_array()
#         files_generated[f"{self.name}_biases.h"] = "biases"
        
#         return files_generated
        
#     def get_function_call(self) -> str:
#         return f"fully_connected_{self.name}(input_buffer_{self.order-1}, output_buffer_{self.order}, {self.name}_weights, {self.name}_biases);"

