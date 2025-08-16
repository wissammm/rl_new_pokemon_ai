import torch
import torch.nn as nn
from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantType, QuantFormat
from onnxruntime.quantization import QDQQuantizer
from onnxruntime.quantization import shape_inference
import numpy as np
import onnx

class DummyCalibrationDataReader(CalibrationDataReader):
    """
    Generates fake calibration data for ONNX quantization.
    """
    def __init__(self, input_names, input_shapes, num_samples=10):
        self.input_names = input_names
        self.input_shapes = input_shapes
        self.num_samples = num_samples
        self.data_iter = self._generate_data()

    def _generate_data(self):
        for _ in range(self.num_samples):
            yield {
                name: np.random.rand(*shape).astype(np.float32)
                for name, shape in zip(self.input_names, self.input_shapes)
            }

    def get_next(self):
        return next(self.data_iter, None)

class FullQuantizer:
    """
    Quantizes an ONNX model using full integer quantization (weights and activations).
    """
    def __init__(self, input_model_path, output_model_path):
        self.input_model_path = input_model_path
        self.output_model_path = output_model_path

    def quantize(self, calibration_data_reader):

        shape_inference.quant_pre_process(self.input_model_path, self.input_model_path, skip_symbolic_shape=False)
        quantize_static(
            model_input=self.input_model_path,
            model_output=self.output_model_path,
            calibration_data_reader=calibration_data_reader,
            quant_format=QuantFormat.QDQ,
            weight_type=QuantType.QInt8,
            activation_type=QuantType.QInt8,
            op_types_to_quantize=["Conv", "MatMul", "Gemm"] ,
            extra_options={
                "ActivationSymmetric": True,
                "WeightSymmetric": True,
                "CalibTensorRangeSymmetric": True,
                "ForceQuantizeNoInputCheck": True,
            }
        )
        return self.output_model_path

    @staticmethod
    def create_fake_calibration_data(onnx_model_path, num_samples=10):
        """
        Loads ONNX model and creates a dummy calibration data reader.
        """
        model = onnx.load(onnx_model_path)
        input_names = [inp.name for inp in model.graph.input]
        input_shapes = [
            [dim.dim_value for dim in inp.type.tensor_type.shape.dim]
            for inp in model.graph.input
        ]
        return DummyCalibrationDataReader(input_names, input_shapes, num_samples)
    
    @staticmethod
    def quantize_array(array, scale, zero_point):
        """
        Quantizes a numpy array using the given scale and zero point.
        """
        quantized = np.round(array / scale + zero_point).astype(np.int8)
        return quantized, scale, zero_point

    @staticmethod
    def dequantize_array(quantized_array, scale, zero_point):
        """
        Dequantizes a numpy array using the given scale and zero point.
        """
        return (quantized_array - zero_point) * scale
