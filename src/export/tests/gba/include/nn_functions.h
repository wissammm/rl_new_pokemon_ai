#ifndef NN_FUNCTIONS_H
#define NN_FUNCTIONS_H
#include <gba_types.h>
// ReLU implementation (previously in relu.h)
static inline void relu_int8_t(int8_t* input, int8_t* output, int size) {
    for(int i = 0; i < size; i++) {
        output[i] = input[i] > 0 ? input[i] : 0;
    }
}

static inline void fc_int8_t(int8_t* input, int8_t* output, const int8_t* weights, const int32_t* biases, int in_size, int out_size) {
    for (int i = 0; i < out_size; i++) {
        int32_t sum = biases[i];
        
        for (int j = 0; j < in_size; j++) {
            sum += (int32_t)weights[i * in_size + j] * input[j];
        }

        // Clip
        if (sum > 127) sum = 127;
        if (sum < -128) sum = -128;
        
        output[i] = (int8_t)sum;
    }
}

static inline void qgemm_int8_t(const int8_t* input, int8_t* output,
                 const int8_t* weights, const int32_t* biases,
                 const int input_size, const int output_size,
                 const int32_t multiplier, const int32_t shift,
                 const int8_t input_zero_point, const int8_t weight_zero_point) {
    
    for (int out_idx = 0; out_idx < output_size; out_idx++) {
        int32_t acc = biases[out_idx];
        
        const int8_t* w = weights + out_idx * input_size;
        
        for (int in_idx = 0; in_idx < input_size; in_idx++) {
            int32_t input_val = input[in_idx] - input_zero_point;
            int32_t weight_val = w[in_idx] - weight_zero_point;
            
            acc += input_val * weight_val;
        }
        
        int64_t requantized;
        if (shift < 0) {
            requantized = ((int64_t)acc * multiplier) >> (-shift);
        } else {
            requantized = ((int64_t)acc * multiplier + (1 << (shift - 1))) >> shift;
        }
        
        if (requantized > 127) {
            requantized = 127;
        }
        if (requantized < -128) {
            requantized = -128;
        }
        
        output[out_idx] = (int8_t)requantized;
    }
}
#endif // NN_FUNCTIONS_H