---
title: "Devlog 2: RMSNorm"
description: "Building the first kernel."
pubDate: "2026-10-XX"
tags: ["Nix", "Rust", "Cuda"]
draft: false
---

The project is being developed at: [rs-inf github](https://github.com/italoaa/rs-inf)

> Quick side note, I am actually writing this like 20 days later. I have already finished
> some other kernels and have lagged a bit behind on the writing of development log but I
> will try to catch up before I finish the major kernels.

This log will be about the RMSNorm Kernel. This kernel computes the following:
$$ y_i = \frac{x_i}{\sqrt{\frac{1}{N}\sum_j x^2_j + \epsilon}} \times \gamma_i $$

The key part of this equation is the sum of squares reduction which is the key part to make this kernel as efficient as possible. This pattern is the reduction pattern and in the PMPP book is covered to a great extent. The key ideas to make sure this kernel runs fast is:
1. Reduce control divergence and coalescing memory access
2. Shared memory to reduce global memory access
3. Warp level primitives

In my first kernel (`v1`) I was able to implement the first to key ideas but not the third. In the following lines I will go through those ideas and will end with some gotchas during development.

## Reducing control divergence and coalescing memory access
Once we start thinking in terms of parallelism we can get the initial idea to approach a reduction is with a tree, which is a good idea, the key comes in how the tree is structured. Lets say we use a simple tree that uses the following to calculate active and inactive threads:
```rust
/// Input: [1, 2, 3, 4, 5, 6, 7]
/// Reduction: ((1+2) + (3 + 4)) + ((5 + 6) + (6 + 7))
/// Launch: for len(x) == N launch N/2 threads in the block
#[kernel]
fn sum(x: &[f32], y: &f32) {
    let tid = thread::threadIdx_x() as usize;
    let block_size = thread::blockDim_x() as usize;

    let mut stride = 1;
    let idx = tid * 2;
    while stride <= block_size {
        if tid % stride == 0 {
            x[idx] += x[idx + stride];
        }
        thread::sync_threads();
        stride *= 2;
    }
    if tid == 0 {
        *y = x[0];
    }
}
```

This reduction kernel will not only have uncoalesced accesses (because threads are `stride` distances from each other and the 2 accesses of each thread are also `stride` distance separated) but as we progress down the reduction (5 iterations) the active threads in the warp will decrease until we have only 1 thread active in a warp, wasting most of the resources allocated.

To improve on this we can use a convergence tree that now makes the first `stride` threads active and the rest inactive:
```rust
/// Input: [1, 2, 3, 4, 5, 6, 7, 8]
/// Reduction: ((1+5) + (3+7)) + ((2+6) + (4+8))
///           = (6 + 10) + (8 + 12)
///           = 36
/// Launch: for len(x) == N launch N/2 threads in the block
#[kernel]
fn sum(x: &[f32], y: &f32) {
    let tid = thread::threadIdx_x() as usize;
    let block_size = thread::blockDim_x() as usize;

    let mut stride = block_size;
    while stride >= 1 {
        if tid < stride {
            x[tid] += x[tid + stride];
        }
        thread::sync_threads();
        stride /= 2;
    }
    if tid == 0 {
        *y = x[0];
    }
}
```

This kernel first coalesces the memory accesses efficiently as neighboring threads accesses neighboring memory locations and second it makes the inactive threads all be crumpled together instead of spread apart allowing the hardware to switch out those warps for active ones.

## Shared memory to reduce global memory access
Now this is much simpler the idea is to instead of pulling from global memory the data each iteration we pull on the first reduction step from global memory but then store back into shared memory then read from there until we finish.

## Some Gotchas
Normally reduction kernels reduce over blocks my problem was that I can't synchronize across blocks to conduct the rest of the operation. Remember that even after the sum of squares reduction we need to do more calculations. If we reduce over blocks we can't be sure the reduction is finished before we continue doing the rest of the operations. Thus in the case of my first kernel I chose to make it a single block reduction with **thread coarsening** to make it possible to reduce inputs larger than 2048 elements.
