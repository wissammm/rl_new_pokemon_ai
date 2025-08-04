#ifndef NN_FUNCTIONS_H
#define NN_FUNCTIONS_H
#include <gba_types.h>
// ReLU implementation (previously in relu.h)
static inline void relu_int8_t(int8_t* input, int8_t* output, int size) {
    for(int i = 0; i < size; i++) {
        output[i] = input[i] > 0 ? input[i] : 0;
    }
}
#endif // NN_FUNCTIONS_H