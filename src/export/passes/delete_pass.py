class DeletePass:
    """
    A pass that deletes a specified node from the graph.
    """

    def __init__(self, node_name: str):
        self.node_name = node_name

    def run(self, graph):
        """
        Apply the delete pass to the graph.
        
        Args:
            graph: The graph to modify.
        """
        for node in graph.nodes:
            if node.name == self.node_name:
                graph.nodes.remove(node)
                print(f"Node '{self.node_name}' has been deleted from the graph.")
                return
        
        print(f"Node '{self.node_name}' not found in the graph.")

class DeleteQuantizePass:
    """
    Deletes all QuantizeLinear and DequantizeLinear nodes from the graph
    and updates tensor references.
    """
    def run(self, graph):
        tensor_remap = {}
        
        for node in graph.node:
            if node.op_type == "QuantizeLinear":
                tensor_remap[node.output[0]] = node.input[0]
            elif node.op_type == "DequantizeLinear":
                tensor_remap[node.output[0]] = node.input[0]
        
        to_remove = [node for node in graph.node if node.op_type in ("QuantizeLinear", "DequantizeLinear")]
        for node in to_remove:
            graph.node.remove(node)
            print(f"Deleted node: {node.name} ({node.op_type})")
        
        for node in graph.node:
            for i, input_name in enumerate(node.input):
                if input_name in tensor_remap:
                    node.input[i] = tensor_remap[input_name]
                    print(f"Remapped input {input_name} → {tensor_remap[input_name]}")
            
            for i, output_name in enumerate(node.output):
                if output_name in tensor_remap:
                    node.output[i] = tensor_remap[output_name]
                    print(f"Remapped output {output_name} → {tensor_remap[output_name]}")