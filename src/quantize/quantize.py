import torch
import torch.nn as nn
from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantType
import numpy as np
import onnx

class SimpleFCNet(nn.Module):
    def __init__(self, input_size=10, fc1_size=8, fc2_size=4):
        super().__init__()
        self.fc1 = nn.Linear(input_size, fc1_size)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(fc1_size, fc2_size)
        self.relu2 = nn.ReLU()

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        x = self.relu2(x)
        return x

def export_to_onnx(model, input_shape, onnx_path):
    model.eval()
    dummy_input = torch.randn(*input_shape)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
        opset_version=17
    )
    print(f"Exported model to {onnx_path}")

# Calibration data reader for static quantization
class RandomDataReader(CalibrationDataReader):
    def __init__(self, input_name, shape, num_batches=10):
        self.input_name = input_name
        self.shape = shape
        self.num_batches = num_batches
        self.data_iter = iter([
            {self.input_name: np.random.randn(*self.shape).astype(np.float32)}
            for _ in range(num_batches)
        ])

    def get_next(self):
        return next(self.data_iter, None)

def quantize_onnx_static(input_model_path, output_model_path, input_name, input_shape):
    dr = RandomDataReader(input_name, input_shape)
    quantize_static(
        model_input=input_model_path,
        model_output=output_model_path,
        calibration_data_reader=dr,
        quant_format="QOperator", 
        weight_type=QuantType.QInt8,
        activation_type=QuantType.QInt8
    )
    print(f"Fully quantized model saved to {output_model_path}")

if __name__ == "__main__":
    model = SimpleFCNet()
    input_shape = (3, 10)  
    onnx_fp32 = "model_fc.onnx"
    export_to_onnx(model, input_shape, onnx_fp32)

    onnx_int8 = "model_fc_int8.onnx"
    quantize_onnx_static(onnx_fp32, onnx_int8, "input", input_shape)