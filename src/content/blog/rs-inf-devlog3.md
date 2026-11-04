---
title: "Devlog 3: RoPE"
description: "Rotary Position Encodings"
pubDate: "2026-11-4"
tags: ["Nix", "Rust", "Cuda"]
draft: false
---

The project is being developed at: [rs-inf github](https://github.com/italoaa/rs-inf)

This log will be about the RoPE Kernel. This kernel is quite interesting and gets quite theoretical so I will do my best in trying to explain it. The main computation done in this kernel is the following:
$$
x_i = x_i\cos\theta_{i,t}-x_{i+D/2}\sin\theta_{i,t}
$$

$$
x_{i+D/2} = x_{i+D/2}\cos\theta_{i,t}+x_i\sin\theta_{i,t}
$$

That computation uses the shape [B,T,H,D] where B is the batch dimension, T is sequence length, H is heads, D is head dimension. From those equations above you might have spotted the similarity to the classic 2d rotation matrix (or deduced it from the title of the computation), but we are doing a 2-dimensional rotation on elements that are $D/2$ elements apart. This is the setup that qwen uses, where it splits the `D` dimension in half and pairs the elements side by side.

Now what exactly is $\theta_{i,t}$? Well we know its a rotation angle that depends on both $t$ and $i$:
$$
\theta_{i,t} = t\omega_i
$$

$$
\omega_i = \frac{1}{\theta^{2i/D}}
$$
where `i` is the position of the element (w.r.t. the D dimension) and `t` is the position in time this token is located at.

We can see first that $\theta$ without a subscript, this is called the **base**. Secondly it is clear that as we move along the time dimension the frequency of $\theta_{i,t}$ increases, this is deliberate, earlier tokens rotate faster. I wont dive deeper as it gets complicated (and i doubt my knowledge hahah) but this makes the rotation relative between two tokens, thus no matter if two tokens appear at the start or end of the sequence the space in between their rotation is the same.

The final thing to note here is that the $cos(\theta_{i,t})$ and $sin(\theta_{i,t})$ values are precomputed and stored in constant memory. Then each thread simply fetches these values. This is done to reduce the workload of calculating these expensive trigonometric function every time the kernel runs. This of course has the compromise that now we must cache these thetas up to a certain `t`, which is now the maximum sequence length we can compute on.
