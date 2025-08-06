from .export_core.graph_loader import ONNXGraphLoader
from .export_core.memory_allocator import MemoryAllocator
from .export_core.exporter_factory import ExporterFactory
from .export_core.code_generator import CodeGenerator
from .passes.pass_manager import PassManager
from .passes.fusion_pass import OperationFusionPass

class ONNXExporter:
    def __init__(self, onnx_path):
        self.onnx_path = onnx_path
        
    def export(self, output_dir="gba"):
        # Load the model
        loader = ONNXGraphLoader(self.onnx_path)
        model = loader.load_model()
        value_info = loader.get_value_info()
        
        # Run optimization passes
        # pass_manager = PassManager(model.graph)
        # pass_manager.add_pass(OperationFusionPass())
        # pass_manager.run_passes()
        # optimized_graph = pass_manager.get_optimized_graph()
        
        allocator = MemoryAllocator(model.graph, value_info)
        allocator.calculate_tensor_sizes()
        allocator.allocate_sequentially()
        
        exporter_factory = ExporterFactory(
            model.graph, 
            value_info, 
            allocator.tensor_offsets
        )
        exporters = exporter_factory.create_exporters()
        
        code_generator = CodeGenerator(exporters, allocator)
        code_generator.generate(output_dir)