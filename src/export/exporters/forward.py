import os
import jinja2
from typing import List, Optional
from ..base import Exporter

class ExportForward(Exporter):
    """Class for exporting forward function implementation and header."""
    
    def __init__(self, template_path: str,
                 call_functions: List[str],
                 inputs: List[str],
                 outputs: List[str],
                 buffer_size: int,
                 include_list: List[str],
                 define_list: List[str],
                 data_type: str = "int8_t",
                 output_path: str = "forward.c"):
        """
        Initialize with the path to a Jinja template and function calls.
        
        Args:
            template_path: Path to the Jinja template file
            call_functions: List of function calls to be included in the forward function
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
        
    def export_forward(self, output_path: Optional[str] = None) -> str:
        """
        Export the forward function to a C source file using the template.
        
        Args:
            output_path: Path where the C source file will be written (optional, uses self.output_path if None)
            
        Returns:
            Path to the generated file
        """
        if output_path is None:
            output_path = self.output_path
            
        params = {
            "include_list": "\n".join(f"#include \"{inc}\"" for inc in self.include_list),
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
        return output_path
    
    def export_forward_header(self, template_path: str, output_path: Optional[str] = None) -> str:
        """
        Export the forward function header file using the template.
        
        Args:
            template_path: Path to the header Jinja template file
            output_path: Path where the header file will be written
            
        Returns:
            Path to the generated file
        """
        if output_path is None:
            output_path = os.path.join(os.path.dirname(self.output_path), "forward.h")
            
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        template = env.get_template(template_name)
        
        params = {
            # "include_list": "\n".join(f"#include \"{inc}\"" for inc in self.include_list),
            "inputs": ", ".join(self.inputs),
            "outputs": ", ".join(self.outputs)
        }
        
        output_content = template.render(**params)
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_path, 'w') as f:
            f.write(output_content)
        
        print(f"Forward function header exported to: {output_path}")
        return output_path