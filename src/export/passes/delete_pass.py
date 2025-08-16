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
        for node in graph.node:
            if node.name == self.node_name:
                graph.node.remove(node)
                print(f"Node '{self.node_name}' has been deleted from the graph.")
                return
        
        print(f"Node '{self.node_name}' not found in the graph.")

class DeleteQuantizePass:
    """
    Deletes QuantizeLinear -> DequantizeLinear pairs from the graph
    and reconnects the inputs/outputs properly.
    """
    def run(self, graph):
        """
        Find and delete QuantizeLinear -> DequantizeLinear pairs,
        reconnecting the graph properly.
        """
        pairs_to_delete = []
        tensor_remap = {}
        
        for quant_node in graph.node:
            if quant_node.op_type == "QuantizeLinear":
                quant_output = quant_node.output[0]
                dequant_node = self._find_consumer(graph, quant_output, "DequantizeLinear")
                
                if dequant_node is not None:
                    pairs_to_delete.append((quant_node, dequant_node))
                    tensor_remap[dequant_node.output[0]] = quant_node.input[0]
        
        nodes_to_remove = []
        for quant_node, dequant_node in pairs_to_delete:
            nodes_to_remove.extend([quant_node, dequant_node])
            print(f"Deleting QuantizeLinear -> DequantizeLinear pair: {quant_node.name} -> {dequant_node.name}")
        
        for node in nodes_to_remove:
            if node in graph.node:
                graph.node.remove(node)
        
        for node in graph.node:
            for i, input_name in enumerate(node.input):
                if input_name in tensor_remap:
                    old_name = input_name
                    new_name = tensor_remap[input_name]
                    node.input[i] = new_name
                    print(f"Remapped input: {old_name} -> {new_name} in node {node.name}")
        
        for i, output in enumerate(graph.output):
            if output.name in tensor_remap:
                old_name = output.name
                new_name = tensor_remap[output.name]
                output.name = new_name
                print(f"Remapped graph output: {old_name} -> {new_name}")
    
    def _find_consumer(self, graph, tensor_name, op_type):
        """Find the node that consumes tensor_name and has the specified op_type"""
        for node in graph.node:
            if node.op_type == op_type and tensor_name in node.input:
                return node
        return None
    
class DeleteFirstLastQuantizeDequantizePass:
    """
    Deletes the first QuantizeLinear/DequantizeLinear pair after input and before output.
    """
    def run(self, graph):
        input_names = {inp.name for inp in graph.input}
        output_names = {out.name for out in graph.output}
        tensor_remap = {}

        for node in graph.node:
            if node.op_type == "QuantizeLinear" and node.input[0] in input_names:
                quant_node = node
                quant_output = quant_node.output[0]
                dequant_node = self._find_consumer(graph, quant_output, "DequantizeLinear")
                if dequant_node:
                    tensor_remap[dequant_node.output[0]] = quant_node.input[0]
                    graph.node.remove(quant_node)
                    graph.node.remove(dequant_node)
                    print(f"Deleted QuantizeLinear/DequantizeLinear after input: {quant_node.name} -> {dequant_node.name}")
                break  # Only first pair

        for node in graph.node:
            if node.op_type == "DequantizeLinear" and node.output[0] in output_names:
                dequant_node = node
                dequant_input = dequant_node.input[0]
                quant_node = self._find_producer(graph, dequant_input, "QuantizeLinear")
                if quant_node:
                    tensor_remap[dequant_node.output[0]] = quant_node.input[0]
                    graph.node.remove(quant_node)
                    graph.node.remove(dequant_node)
                    print(f"Deleted QuantizeLinear/DequantizeLinear before output: {quant_node.name} -> {dequant_node.name}")
                break  # Only first pair

        for node in graph.node:
            for i, input_name in enumerate(node.input):
                if input_name in tensor_remap:
                    node.input[i] = tensor_remap[input_name]

        for output in graph.output:
            if output.name in tensor_remap:
                output.name = tensor_remap[output.name]

    def _find_consumer(self, graph, tensor_name, op_type):
        for node in graph.node:
            if node.op_type == op_type and tensor_name in node.input:
                return node
        return None

    def _find_producer(self, graph, tensor_name, op_type):
        for node in graph.node:
            if node.op_type == op_type and tensor_name in node.output:
                return node
        return None
    
class DeleteFirstInputQDQPass:
    """
    Deletes only the first QuantizeLinear -> DequantizeLinear pair immediately after the input.
    """
    def run(self, graph):
        input_names = {inp.name for inp in graph.input}
        tensor_remap = {}

        for node in graph.node:
            if node.op_type == "QuantizeLinear" and node.input[0] in input_names:
                quant_node = node
                quant_output = quant_node.output[0]
                dequant_node = self._find_consumer(graph, quant_output, "DequantizeLinear")
                if dequant_node:
                    # Remap output of dequant to input of quant
                    tensor_remap[dequant_node.output[0]] = quant_node.input[0]
                    graph.node.remove(quant_node)
                    graph.node.remove(dequant_node)
                    print(f"Deleted first QDQ pair after input: {quant_node.name} -> {dequant_node.name}")
                break  # Only the first pair

        for node in graph.node:
            for i, input_name in enumerate(node.input):
                if input_name in tensor_remap:
                    node.input[i] = tensor_remap[input_name]

        for output in graph.output:
            if output.name in tensor_remap:
                output.name = tensor_remap[output.name]

    def _find_consumer(self, graph, tensor_name, op_type):
        for node in graph.node:
            if node.op_type == op_type and tensor_name in node.input:
                return node
        return None