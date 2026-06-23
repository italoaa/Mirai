---
title: "Rusty Flow"
description: "A (almost) dependency-free autodiff tensor library in Rust built for education and exploration"
pubDate: "2025-05-08"
draft: false
tags: ["Project"]
featured: false
---

# Project
This project aims to replicate the Pytorch's api for tensor operations and auto differentiation

# Experience
This project was initially motivated by [Andrej Karpathy](https://www.youtube.com/andrejkarpathy) video on back-propagation, where he built a auto differentiation project but for single values. Using this as a basis I thought that extending this to tensors would be straight forward but .... it wasn't as easy as I though (as always).

The full code project was divided on the Tensor Operations and the Auto Differentiation of these operations. Implementing the initial parts of the library was quite simple following [Edward Z. Yang](https://blog.ezyang.com/2019/05/pytorch-internals/) blog post on PyTorch internals i mimicked their methodologies. These mainly included storing the tensor as a flat array and having the values of its shape and strides separately.

After building the foundation, (operations add, subtract, etc. and their backwards versions), the next challenge was broadcasting. Broadcasting in PyTorch, allows for tensors of different shapes to be used in operations together. This is a powerful abstraction, as it allows you to do the following:
```python
a = torch.randn(3, 4)
b = torch.randn(4)
c = a + b
```

Where the tensor b is broadcasted from [1, 4] -> [3, 4] by repeating the values of b 3 times. The implementation of this was not simple. Having to translate from multidimensional indices to flat indices was tough! But it did force me to have a deep understanding of how this process is done. In short in the tensor object we store a `strides` vector, which tells us how many places to move (in a flat array) to get to the next element in that dimension. For example, if we have a tensor of shape (3, 4) and strides (4, 1), to move one element in the first dimension we need to move 4 places in the flat array, and to move one element in the second dimension we need to move 1 place. Using this and an iterator in Rust we can generate the corresponding indices for the tensors in the operation through their broadcasted shape.

But it does not end there! Once the shapes can be broadcasted, we need to implement the backwards pass. This is where the fun begins! The backwards pass now needs to be aware of this broadcasting and the gradients should flow accordingly. This was a bit tricky, as in some operations the input tensors must be operated with the gradients, which could be of a different shape. This meant broadcasting had to also happen in the backwards pass, and once the gradients are calculated accordingly they should be UN-broadcasted back to the original shape.

All good fun! Although hard to implement, I enjoyed it a lot!

<!-- Local Variables: -->
<!-- jinx-local-words: "broadcasted" -->
<!-- End: -->
