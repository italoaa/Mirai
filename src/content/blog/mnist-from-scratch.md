---
title: "MNSIT from Scratch"
description: "The journey of building a MLP from scratch using CUDA"
pubDate: "2025-05-08"
tags: ["Project"]
draft: false
---

# Project
The idea for the project was to dive into the basics of GPU programming by building a MLP in CUDA!

# Experience
I was initially motivated to do this by [Simon Oz](https://www.youtube.com/@szymonozog7862) youtube playlist on GPU programming. I wanted to apply what I was learning and thought to follow his steps and build an MLP.

At the start I was just getting used to the way CUDA works and how kernels are used. This was the first time I had touched any GPU programming projects so this part took a while. I specially struggled with the way multidimensional indices are flattened. 

```cuda
__global__ void forward(int bs, int n, int out_w,
			float* input, float* weights, float* biases, float* output) {
  // y for rows (height of the mat)
  int row = blockIdx.y * blockDim.y + threadIdx.y; 
  // x for column (width of the mat)
  int column = blockIdx.x * blockDim.x + threadIdx.x; 

  // do the dot product between the row and col
  if (row < bs && column < out_w) {
    output[row*out_w + column] = biases[column];
    for (int i = 0; i < n; i++) {
      output[row * out_w + column] += weights[i * out_w + column] * input[row * n + i];
    }
  }
}
```

The kernel above indexes into the data with the row and column variables turning them into flat indices. This was the hardest part to get used to as I had to deconstruct my mental model of multidimensional arrays, and replace it with flat ones and flat indices.

To solidify this I have actually built a Tensor library that forced me to practice this called [Rusty Flow](https://github.com/italoaa/Rusty-Flow) although it is not in cuda all cpu.

I am very happy to peel of the layers in machine learning and look into how things work at a deeper level.
