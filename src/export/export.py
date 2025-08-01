import os
import jinja2
from typing import Dict, Any, List, Optional, Union

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

class ExportParameters(Exporter):
    def export_array(self, 
                    array_data: Union[List[Any], str],
                    array_name: str,
                    memory_region: str = "const", 
                    datatype: str = "int8_t",
                    output_path: str = "array_names.h") -> None:
        """
        Export an array to a C header file using the template.
        
        Args:
            array_data: The data for the array (either a list or formatted string)
            array_name: Name of the array variable
            memory_region: Memory region specifier (e.g., "const", "static")
            datatype: C data type (e.g., "int", "float")
            output_path: Path where the header file will be written
        """
        if isinstance(array_data, list):
            formatted_data = "{" + ", ".join(str(item) for item in array_data) + "}"
        else:
            formatted_data = array_data
            
        params = {
            "memory_region": memory_region,
            "datatype": datatype,
            "array_name": array_name,
            "data": formatted_data
        }
        
        output_content = self.template.render(**params)
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_path, 'w') as f:
            f.write(output_content)
            
        print(f"Successfully exported array '{array_name}' to {output_path}")