import onnx
from onnx import shape_inference

class ONNXGraphLoader:
    def __init__(self, onnx_path):
        self.onnx_path = onnx_path
        self.model = None
        self.value_info = {}
        
    def load_model(self):
        """Load and preprocess ONNX model"""
        self.model = onnx.load(self.onnx_path)
        try:
            inferred_model = shape_inference.infer_shapes(self.model)
            self.model = inferred_model
        except Exception as e:
            print(f"Warning: Shape inference failed: {e}")
        
        self._extract_value_info()
        
        return self.model
    
    def _extract_value_info(self):
        """Extract tensor shape information from the model"""
        self.value_info = {}
        
        for vi in self.model.graph.input:
            self.value_info[vi.name] = vi
            
        for vi in self.model.graph.output:
            self.value_info[vi.name] = vi
            
        for vi in self.model.graph.value_info:
            self.value_info[vi.name] = vi

        if len(self.value_info) < len(self.model.graph.node) + 1:
            self._derive_missing_value_info()
    
    def _derive_missing_value_info(self):
        """Derive missing shape info from the graph structure"""
        for node in self.model.graph.node:
            for output_name in node.output:
                if output_name not in self.value_info:
                    for input_name in node.input:
                        if input_name in self.value_info:
                            print(f"Warning: Derived shape for {output_name} from {input_name}")
                            self.value_info[output_name] = self.value_info[input_name]
                            break
    
    def get_value_info(self):
        """Get the value info dictionary"""
        if not self.model:
            self.load_model()
            
        if not self.value_info:
            print("Warning: No value info was extracted from the model!")
            
        return self.value_info