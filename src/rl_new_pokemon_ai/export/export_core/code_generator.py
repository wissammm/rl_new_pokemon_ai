import os
from ..exporters.forward import ExportForward

class CodeGenerator:
    """Generates C code from layer exporters"""
    
    def __init__(self, exporters, allocator):
        self.exporters = exporters['exporters']
        self.function_calls = exporters['function_calls']
        self.defines = exporters['defines'] 
        self.include_list = exporters['includes']
        self.allocator = allocator
        
    def generate(self, output_dir, source_subdir="source", include_subdir="include"):
        """
        Generate C code for the model
        """
        source_dir = os.path.join(output_dir, source_subdir)
        include_dir = os.path.join(output_dir, include_subdir)
        
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(include_dir, exist_ok=True)
        
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "templates", "forward.jinja"
        )
        
        header_template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "templates", "forward_header.jinja"
        )
        
        template_parameters_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "templates", "parameters.jinja"
        )
        
        for exporter in self.exporters:
            exporter.template_path = template_parameters_path
            exporter.export_layer(include_dir)
            print(f"Exported layer {exporter.name} parameters to {include_dir}")
        
        # Generate forward function
        c_output_path = os.path.join(source_dir, "forward.c")
        h_output_path = os.path.join(include_dir, "forward.h")
        
        forward_exporter = ExportForward(
            template_path=template_path,
            call_functions=self.function_calls,
            inputs=["int8_t *input"],
            outputs=["int8_t *output"],
            buffer_size=self.allocator.total_buffer_size,
            include_list=self.include_list,
            define_list=self.defines,
            data_type="int8_t",
            output_path=c_output_path
        )
        
        forward_exporter.export_forward()
        forward_exporter.export_forward_header(header_template_path, h_output_path)