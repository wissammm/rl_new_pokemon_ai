class MemoryAllocator:
    def __init__(self, graph, value_info):
        self.graph = graph
        self.value_info = value_info
        self.tensor_sizes = {}
        self.tensor_offsets = {}
        
    def calculate_tensor_sizes(self):
        """Calculate size in elements for each tensor"""
        self.tensor_sizes = {}
        for name, vi in self.value_info.items():
            shape = vi.type.tensor_type.shape
            size = 1
            for dim in shape.dim:
                size *= dim.dim_value
            self.tensor_sizes[name] = size

    def allocate_sequentially(self):
        """Simple sequential allocation"""
        self.tensor_offsets = {}
        current_offset = 0

        for node in self.graph.node:
            for output_name in node.output:
                if output_name not in [o.name for o in self.graph.output]:
                    if output_name in self.tensor_sizes:
                        self.tensor_offsets[output_name] = current_offset
                        current_offset += self.tensor_sizes[output_name]
                    else:
                        print(f"Warning: Skipping tensor '{output_name}' - not in tensor_sizes")

        self.total_buffer_size = current_offset
        
    def allocate_with_reuse(self):
        """Advanced allocation with memory reuse"""
        #TODO : Implement memory reuse logic
        raise NotImplementedError("Memory reuse logic is not implemented yet.")
