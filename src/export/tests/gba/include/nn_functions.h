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
#endif // NN_FUNCTIONS_H