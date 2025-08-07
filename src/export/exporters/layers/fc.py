import os
import numpy as np
from typing import Dict, List, Tuple
from ...enums import CallPosition
from ...exporters.parameters import ExportParameters
from .layer_base import BaseLayerExporter

class FullyConnectedExporter(BaseLayerExporter):
    """Exporter for fully connected (dense) layers."""
    def __init__(self, name, input_shape, output_shape, input_idx, output_idx, 
                 datatype="int8_t", call_position=CallPosition.BETWEEN):
        super().__init__(name, input_shape, output_shape, input_idx, output_idx, 
                         datatype, call_position)
        self.weights = None
        self.biases = None
    
    
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

    
    def get_defines(self):
        defines = super().get_defines()
        defines.extend([
            f"{self.name}_IN_SIZE {self.input_shape[-1]}",
            f"{self.name}_OUT_SIZE {self.output_shape[-1]}",
        ])
        return defines
    
    def get_function_call(self):
        """Generate function call with requantization parameters"""
        input_param = self._get_input_param()
        output_param = self._get_output_param()
        return f"fc_{self.datatype}({input_param}, {output_param}, {self.name}_weights, {self.name}_biases, {self.name}_IN_SIZE, {self.name}_OUT_SIZE);"
    



class QGemmExporter(BaseLayerExporter):
    """Exporter for QGemm (Quantized General Matrix Multiplication) layers."""
    def __init__(self, name, input_shape, output_shape, input_idx, output_idx, 
                datatype="int8_t", call_position=CallPosition.BETWEEN):
        super().__init__(name, input_shape, output_shape, input_idx, output_idx, 
                        datatype, call_position)
        self.weights = None
        self.biases = None
        
        # Quantization parameters
        self.input_scale = None
        self.weight_scale = None
        self.output_scale = None
        
        self.input_zero_point = 0  
        self.weight_zero_point = 0 
        self.bias_zero_point = 0  
        
        self.multiplier = None
        self.shift = None
    
    def set_quantization_params(self, input_scale, weight_scale, output_scale, 
                               input_zero_point=0, weight_zero_point=0, bias_zero_point=0):
        """Set quantization parameters and compute requantization factors"""
        self.input_scale = input_scale
        self.weight_scale = weight_scale
        self.output_scale = output_scale
        
        self.input_zero_point = input_zero_point
        self.weight_zero_point = weight_zero_point
        self.bias_zero_point = bias_zero_point
        
        self.multiplier, self.shift = self.compute_requantize_params(
            input_scale, weight_scale, output_scale)
    
    def compute_requantize_params(self, input_scale, weight_scale, output_scale):
        """
        Compute multiplier and shift for requantization
        
        The effective scale for requantization is (input_scale * weight_scale / output_scale)
        We convert this to a fixed-point multiplication with a power-of-2 shift.
        """
        if input_scale is None or weight_scale is None or output_scale is None:
            return None, None
            
        effective_scale = (input_scale * weight_scale) / output_scale
        
        shift = 0
        while effective_scale * (1 << shift) < (1 << 30) and shift < 31:
            shift += 1
        shift -= 1  
        
        multiplier = int(round(effective_scale * (1 << shift)))
        
        return multiplier, shift
    
    def get_include(self) -> List[str]:
        """Return a list of header filenames required for this layer"""
        return [
            f"{self.name.lower()}_weights.h",
            f"{self.name.lower()}_biases.h"
        ]
    
    def export_layer(self, output_dir: str) -> Dict[str, str]:
        """
        Export QGemm layer weights and biases as arrays.
        
        Args:
            output_dir: Directory where files should be saved
            
        Returns:
            Dictionary of generated files
        """
        if not isinstance(self.weights, np.ndarray) or not isinstance(self.biases, np.ndarray):
            raise TypeError(f"Weights and biases must be numpy ndarrays for {self.name}")
  
        files_generated = {}

        weights_path = os.path.join(output_dir, f"{self.name.lower()}_weights.h")
        weights_1d = self.weights.flatten().astype(np.int8)  # Use int8 for quantized weights
        weights_exporter = ExportParameters(
            template_path=self.template_path,
            array_data=weights_1d,
            array_name=f"{self.name}_weights",
            memory_region="",
            datatype="int8_t",  # Explicitly set int8_t for weights
            output_path=weights_path
        )
        weights_file = weights_exporter.export_array()
        files_generated["weights"] = weights_file

        biases_path = os.path.join(output_dir, f"{self.name.lower()}_biases.h")
        biases_1d = self.biases.flatten().astype(np.int32)  # Use int32 for quantized biases
        biases_exporter = ExportParameters(
            template_path=self.template_path,
            array_data=biases_1d,
            array_name=f"{self.name}_biases",
            memory_region="",
            datatype="int32_t",  # Explicitly set int32_t for biases
            output_path=biases_path
        )
        biases_file = biases_exporter.export_array()
        files_generated["biases"] = biases_file

        print(f"Exported QGemm layer parameters for {self.name}")
        return files_generated
    
    def get_defines(self) -> List[str]:
        """Return a list of #define statements required for this layer"""
        defines = super().get_defines()
        defines.extend([
            f"{self.name}_IN_SIZE {self.input_shape[-1]}",
            f"{self.name}_OUT_SIZE {self.output_shape[-1]}",
            f"{self.name}_INPUT_SCALE {self.input_scale}f",
            f"{self.name}_WEIGHT_SCALE {self.weight_scale}f",
            f"{self.name}_OUTPUT_SCALE {self.output_scale}f",
            f"{self.name}_INPUT_ZERO_POINT {self.input_zero_point}",
            f"{self.name}_WEIGHT_ZERO_POINT {self.weight_zero_point}",
            f"{self.name}_BIAS_ZERO_POINT {self.bias_zero_point}",
            f"{self.name}_MULTIPLIER {self.multiplier}",
            f"{self.name}_SHIFT {self.shift}",
        ])
        return defines
    
    def get_function_call(self) -> str:
        """Generate function call for the QGemm operation"""
        input_param = self._get_input_param()
        output_param = self._get_output_param()
        
        return (f"qgemm_{self.datatype}({input_param}, {output_param}, "
                f"{self.name}_weights, {self.name}_biases, "
                f"{self.name}_IN_SIZE, {self.name}_OUT_SIZE, "
                f"{self.name}_MULTIPLIER, {self.name}_SHIFT, "
                f"{self.name}_INPUT_ZERO_POINT, {self.name}_WEIGHT_ZERO_POINT);")