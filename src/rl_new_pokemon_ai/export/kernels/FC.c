#include <stdint.h> //need to be replaced by gba_types.h

void fully_connected_int8(
    int8_t* input,
    int32_t* output,
    int8_t* weights,
    int32_t* bias,
    int input_size,
    int output_size
) 
{
    for (int i = 0; i < output_size; ++i) {
        int32_t acc = bias[i];
        for (int j = 0; j < input_size; ++j) {
            acc += weights[i * input_size + j] * input[j]; 
        output[i] = acc;
    }
}