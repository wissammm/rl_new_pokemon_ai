from typing import Tuple, List
from ...base import LayerExporter
from ...enums import CallPosition

class BaseLayerExporter(LayerExporter):
    """Base implementation for layer exporters with common functionality."""
    
    def __init__(self, 
                 name: str, 
                 input_shape: Tuple[int, ...], 
                 output_shape: Tuple[int, ...],
                 input_idx: int = 0, 
                 output_idx: int = 0,
                 datatype: str = "int8_t",
                 call_position: CallPosition = CallPosition.BETWEEN):
        """
        Initialize base layer exporter.
        
        Args:
            name: Layer name
            input_shape: Shape of input tensor
            output_shape: Shape of output tensor
            input_idx: Input buffer index
            output_idx: Output buffer index
            datatype: C data type
            call_position: Position in the call chain
        """
        self.name = name.replace("/", "_").upper()
        self.input_shape = input_shape
        self.output_shape = output_shape
        self.input_idx = input_idx
        self.output_idx = output_idx
        self.datatype = datatype
        self.call_position = call_position
    
    def _get_input_param(self) -> str:
        """Get the input parameter based on call position."""
        if self.call_position in (CallPosition.FIRST, CallPosition.BOTH):
            return "input"
        else:
            return f"mem_buffer + {self.name}_INPUT_IDX"
    
    def _get_output_param(self) -> str:
        """Get the output parameter based on call position."""
        if self.call_position in (CallPosition.LAST, CallPosition.BOTH):
            return "output"
        else:
            return f"mem_buffer + {self.name}_OUTPUT_IDX"
    
    def get_defines(self) -> List[str]:
        """Get common define statements for layers."""
        return [
            f" {self.name}_INPUT_IDX {self.input_idx}",
            f" {self.name}_OUTPUT_IDX {self.output_idx}",
        ]