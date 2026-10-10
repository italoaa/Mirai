---
title: "Devlog 2: RMSNorm"
description: "Building the first kernel."
pubDate: "2026-10-XX"
tags: ["Nix", "Rust", "Cuda"]
draft: true
---

The project is being developed at: [rs-inf github](https://github.com/italoaa/rs-inf)

- had to learn reductions
- at first thought that I should reduce the kernel over any blocks but then ifound thread coarsening as a pre reduction step to do the reduction in a single block
- this allowed me to fuse everything into a single kernel
- used dynamic memory to make the testing of this kernel later with many block sizes easier later
- avoided disjoint slices for now i am not used to them.
- chapter 10 in pmpp
- I can still improve the performance with warp level instructions

future work:
- improve the testing (mention how i landed on the issue with #[cfg(test)] and how it just did not allow me to use atomics)
- now that i do not use atomics maybe i can go back to the previous way of testing
- appart from correctness testing i should also have a performance test too.
