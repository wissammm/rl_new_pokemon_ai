import onnx
from onnx import helper
from onnx import numpy_helper

class GemmQuantDequantFusionPass:
    def run(self, graph):
        """
        Fuse Gemm -> QuantizeLinear -> DequantizeLinear into QGemmCustom
        """
        nodes_to_remove = []
        nodes_to_add = []
        
        for i, node in enumerate(graph.node):
            if node.op_type == 'Gemm':
                quant_node = self._find_next_node_by_input(graph, node.output[0], 'QuantizeLinear')
                if quant_node is None:
                    continue
                    
                dequant_node = self._find_next_node_by_input(graph, quant_node.output[0], 'DequantizeLinear')
                if dequant_node is None:
                    continue
                
                fused_node = self._create_qgemm_custom_node(node, quant_node, dequant_node)
                nodes_to_add.append(fused_node)
                
                nodes_to_remove.extend([node, quant_node, dequant_node])
        
        for node in nodes_to_remove:
            if node in graph.node:
                graph.node.remove(node)
        
        for node in nodes_to_add:
            graph.node.append(node)
    
    def _find_next_node_by_input(self, graph, output_name, op_type):
        """Find the next node that uses output_name as input and has the specified op_type"""
        for node in graph.node:
            if node.op_type == op_type and output_name in node.input:
                return node
        return None
    
    def _create_qgemm_custom_node(self, gemm_node, quant_node, dequant_node):
        """Create a QGemmCustom node from Gemm, QuantizeLinear, and DequantizeLinear nodes"""
        
        inputs = list(gemm_node.input)
        
        if len(quant_node.input) > 1:
            inputs.append(quant_node.input[1])  # y_scale
        if len(quant_node.input) > 2:
            inputs.append(quant_node.input[2])  # y_zero_point
        

        if len(dequant_node.input) > 1:
            inputs.append(dequant_node.input[1])  # x_scale
        if len(dequant_node.input) > 2:
            inputs.append(dequant_node.input[2])  # x_zero_point
        
        outputs = list(dequant_node.output)
        
        attributes = []
        
        for attr in gemm_node.attribute:
            attributes.append(attr)
        
        for attr in quant_node.attribute:
            new_attr = helper.make_attribute(f"quant_{attr.name}", attr)
            attributes.append(new_attr)
        
        for attr in dequant_node.attribute:
            new_attr = helper.make_attribute(f"dequant_{attr.name}", attr)
            attributes.append(new_attr)
        
        fused_node = helper.make_node(
            'QGemmCustom',
            inputs=inputs,
            outputs=outputs,
            name=f"{gemm_node.name}_fused" if gemm_node.name else "qgemm_custom_fused",
            **{attr.name: self._get_attribute_value(attr) for attr in attributes}
        )
        
        return fused_node
    
    def _get_attribute_value(self, attr):
        """Extract the value from an ONNX attribute"""
        if attr.type == onnx.AttributeProto.FLOAT:
            return attr.f
        elif attr.type == onnx.AttributeProto.INT:
            return attr.i
        elif attr.type == onnx.AttributeProto.STRING:
            return attr.s
        elif attr.type == onnx.AttributeProto.TENSOR:
            return attr.t
        elif attr.type == onnx.AttributeProto.FLOATS:
            return list(attr.floats)
        elif attr.type == onnx.AttributeProto.INTS:
            return list(attr.ints)
        elif attr.type == onnx.AttributeProto.STRINGS:
            return list(attr.strings)
        elif attr.type == onnx.AttributeProto.TENSORS:
            return list(attr.tensors)
        else:
            return None
        
class QGemmReluFusionPass:
    def run(self, graph):
        """
        Fuse QGemmCustom -> Relu into QGemmReluCustom
        """
        nodes_to_remove = []
        nodes_to_add = []
        
        for node in graph.node:
            if node.op_type == 'QGemmCustom':
                relu_node = self._find_next_node_by_input(graph, node.output[0], 'Relu')
                if relu_node is None:
                    continue
                
                fused_node = self._create_qgemm_relu_custom_node(node, relu_node)
                nodes_to_add.append(fused_node)
                
                nodes_to_remove.extend([node, relu_node])
        
        for node in nodes_to_remove:
            if node in graph.node:
                graph.node.remove(node)
        
        for node in nodes_to_add:
            graph.node.append(node)
    
    def _find_next_node_by_input(self, graph, output_name, op_type):
        """Find the next node that uses output_name as input and has the specified op_type"""
        for node in graph.node:
            if node.op_type == op_type and output_name in node.input:
                return node
        return None
    
    def _create_qgemm_relu_custom_node(self, qgemm_node, relu_node):
        """Create a QGemmReluCustom node from QGemmCustom and Relu nodes"""
        
        inputs = list(qgemm_node.input)
        
        outputs = list(relu_node.output)
        
        attributes = []
        for attr in qgemm_node.attribute:
            attributes.append(attr)
        
        for attr in relu_node.attribute:
            new_attr = helper.make_attribute(f"relu_{attr.name}", attr)
            attributes.append(new_attr)
        
        fused_node = helper.make_node(
            'QGemmReluCustom',
            inputs=inputs,
            outputs=outputs,
            name=f"{qgemm_node.name}_relu_fused" if qgemm_node.name else "qgemm_relu_custom_fused",
            **{attr.name: self._get_attribute_value(attr) for attr in attributes}
        )
        
        return fused_node
    
    def _get_attribute_value(self, attr):
        """Extract the value from an ONNX attribute"""
        if attr.type == onnx.AttributeProto.FLOAT:
            return attr.f
        elif attr.type == onnx.AttributeProto.INT:
            return attr.i
        elif attr.type == onnx.AttributeProto.STRING:
            return attr.s
        elif attr.type == onnx.AttributeProto.TENSOR:
            return attr.t
        elif attr.type == onnx.AttributeProto.FLOATS:
            return list(attr.floats)
        elif attr.type == onnx.AttributeProto.INTS:
            return list(attr.ints)
        elif attr.type == onnx.AttributeProto.STRINGS:
            return list(attr.strings)
        elif attr.type == onnx.AttributeProto.TENSORS:
            return list(attr.tensors)
        else:
            return None
        
