import os
from typing import List, Any, Union
from ..base import Exporter

class ExportParameters(Exporter):
    """Class for exporting array parameters to C header files."""
    
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

    def export_array(self) -> str:
        """
        Export an array to a C header file using the template.
        
        Returns:
            Path to the generated file
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
            
        return self.output_path