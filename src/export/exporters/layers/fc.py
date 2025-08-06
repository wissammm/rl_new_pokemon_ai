import os
import numpy as np
from typing import Dict, List, Tuple
from ...enums import CallPosition
from ...exporters.parameters import ExportParameters
from .layer_base import BaseLayerExporter

class FullyConnectedExporter(BaseLayerExporter):
    """Exporter for fully connected (dense) layers."""
    
    def __init__(self, 
                 name: str,
                 input_shape: Tuple[int, ...], 
                 output_shape: Tuple[int, ...], 
                 input_idx: int = 0, 
                 output_idx: int = 0, 
                 datatype: str = "int8_t", 
                 call_position: CallPosition = CallPosition.BETWEEN,
                 template_path: str = None):
        """
        Initialize FC layer exporter.
        
        Args:
            name: Layer name
            input_shape: Shape of input tensor
            output_shape: Shape of output tensor
            input_idx: Input buffer index
            output_idx: Output buffer index
            datatype: C data type
            call_position: Position in the call chain
            template_path: Path to the template for exporting parameters
        """
        super().__init__(name, input_shape, output_shape, input_idx, output_idx, datatype, call_position)
        self.template_path = template_path
        # These will be populated when we process the ONNX model
        self.weights = None
        self.biases = None
    
    def get_function_call(self) -> str:
        """Get the C function call for the FC layer."""
        input_param = self._get_input_param()
        output_param = self._get_output_param()
        
        return f"fc_{self.datatype}({input_param}, {output_param}, {self.name}_weights, {self.name}_biases, {self.name}_IN_SIZE, {self.name}_OUT_SIZE);"
    
    def get_defines(self) -> List[str]:
        """Get the list of defines for the FC layer."""
        base_defines = super().get_defines()
        return base_defines + [
            f" {self.name}_IN_SIZE {self.input_shape[1]}",
            f" {self.name}_OUT_SIZE {self.output_shape[1]}",
        ]
    
    def get_include(self) -> List[str]:
        """Return a list of header filenames required for this layer """
        return [
            f"{self.name.lower()}_weights.h",
            f"{self.name.lower()}_biases.h"
        ]
    
    def export_layer(self, output_dir: str) -> Dict[str, str]:
        """
        Export FC layer weights and biases as 1D numpy arrays.
        
        Args:
            output_dir: Directory where files should be saved
            
        Returns:
            Dictionary of generated files
        """

        if not isinstance(self.weights, np.ndarray) or not isinstance(self.biases, np.ndarray):
            raise TypeError(f"Weights and biases must be numpy ndarrays for {self.name}")
  
        files_generated = {}

        weights_path = os.path.join(output_dir, f"{self.name.lower()}_weights.h")
        weights_1d = self.weights.flatten().astype(np.int32) 
        weights_exporter = ExportParameters(
            template_path=self.template_path,
            array_data=weights_1d,
            array_name=f"{self.name}_weights",
            memory_region="",
            datatype=self.datatype,
            output_path=weights_path
        )
        weights_file = weights_exporter.export_array()
        files_generated["weights"] = weights_file

        biases_path = os.path.join(output_dir, f"{self.name.lower()}_biases.h")
        biases_1d = self.biases.flatten().astype(np.int32)
        biases_exporter = ExportParameters(
            template_path=self.template_path,
            array_data=biases_1d,
            array_name=f"{self.name}_biases",
            memory_region="",
            datatype="int32_t",
            output_path=biases_path
        )
        biases_file = biases_exporter.export_array()
        files_generated["biases"] = biases_file

        print(f"Exported FC layer parameters for {self.name}")
        return files_generated