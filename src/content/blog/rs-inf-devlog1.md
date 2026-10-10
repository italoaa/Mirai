---
title: "Devlog 1: Introduction to Rs-inf"
description: "Building the development setup."
pubDate: "2026-10-09"
tags: ["Nix", "Rust", "Cuda"]
draft: false
---

The project is being developed at: [rs-inf github](https://github.com/italoaa/rs-inf)

# What is Rs-inf
Like the name suggest this project is a simple inference engine with rust. The kicker of this project is the use of the [cuda-oxide](https://github.com/NVIDIA/cuda-rust/tree/main/cuda-oxide) crate, which is quite new. It allows you to write CUDA (SIMT) kernels but in pure rust and this project will take advantage of that. As a side note I will be reading the legendary Programming Massively Parallel Processors (5th edition) to really learn these concepts well.

The initial objective for this project, at least as of writing this post, is to be able to run a Qwen3 dense model (not even efficiently). That is it. Even though this might sound unambitious I think it really is. If we take into consideration that: I have very little experience with cuda, will not use any coding agent (after all this is mostly to learn) and I am not fully updated with the latest LLM model architectures I think this is a good initial goal to set. The nice thing about this project through is that progression is measurable and quite clear. We just have to go fast.

# The development environment
So these are great plans but there is a problem: I do not have an nvidia GPU. Thus my solution is to use [vast.ai](https://vast.ai) to rent development boxes with GPUs and be able to program them. Now I know what you are thinking, Remote development? That sounds like a pain, well it would be but I have one trick up my sleeve.

The trick? Nix. So basically lets drill down to why remote development is a pain:
1. Bad connection
2. Aligning dependencies is hard
3. The iteration time is slow

The first one is simple, just rent boxes physically close to you. So in my case I will just rent machines in Europe. The second is more nuanced so I will defer it for later, and the third can be solved by having automatic sync and test watchers. These watchers will from the instance a change is made locally, propagate that change to the remote and test the new change ASAP.

Currently I have implemented a development workflow that I am happy with, even though it still needs more work, it does what I mentioned above and lets me iterate fast. Most of my first week was spent on getting this setup ready so its was not simple to me. Now lets get to solving the second issue.

## Deterministic Environment
I can't stress enough the importance of having a deterministic environment that is the same no matter **when** and **where** it runs. I think in a project like this where we need to juggle all of the following:
1. Host Cuda driver
2. Cuda Toolkit
3. cuda-oxide compatibility
4. dynamic linking paths
5. Hardware compatibility

And keep them all aligned ... nix becomes kind of the only option, I will go deeper into detail later but this is one of the features of the development environment.

### DevShells and provisioning the DevBox
Now having development spread out between `x86_64-linux` and `x86_64-darwin` machines I can build development shells for each system with nix. In the flake I built a devShell for each system having the main one being `x86_64-linux`, and then `x86_64-darwin` could spin up a docker container based on `nixos/nix` image (also pinned) and start the `linux` dev shell within. The linux shell inherits `cuda-oxide`'s startup hook so it handles checking the dependencies and making sure everything is aligned (also pinned).

Furthermore, the project has a `secrets.env` that holds the api key to vast. This file is encrypted using sops (of course) and during the startup of the dev shell we decrypt and load the secrets to the environment. With the secrets loaded we can make a request to vast to list all the available GPUs for us to use:

```sh
  #  ID        CUDA   N  Model        PCIE  cpu_ghz  vCPUs   RAM  VRAM  Disk  $/hr    DLP   DLP/$   score  NV Driver   Net_up  Net_down  R     Max_Days  mach_id  status
  1  50865915  13.0  1x  GTX_1080_Ti  6.0   3.4      4.0    15.9  11.3  184   0.0617  5.5   88.42   41.8   580.173.02  828.8   861.8     99.2  87.8      150049   verified
  2  48105707  13.0  1x  RTX_3060     6.5   3.3      4.0    20.0  12.3  365   0.0743  10.3  138.65  79.9   580.173.02  684.8   517.8     98.7  14.0      141044   verified
  3  47893736  13.0  1x  RTX_3060     12.7  3.8      12.0   15.8  12.3  287   0.0743  10.3  139.16  86.8   580.173.02  903.4   837.4     99.4  14.0      145862   verified
  4  46810398  13.0  1x  RTX_3060     12.5  3.5      8.0    16.0  12.3  51    0.0814  12.3  150.69  100.7  580.159.03  882.4   915.2     99.8  122.9     142642   verified
  5  45010918  13.0  1x  RTX_3060_Ti  12.7  4.3      12.0   32.0   8.2  246   0.0947  11.3  119.65  68.0   580.173.02  912.4   898.4     99.5  14.0      144185   verified
  6  53170012  13.2  1x  RTX_3060_Ti  24.1  4.7      24.0   15.9   8.2  416   0.0971  14.0  143.98  80.8   595.91.07   736.1   884.4     99.4  180.0     56006    verified
```

Say we want to use the RTX_3060 with id `46810398`, we can simply run:
```sh
just vast-start 46810398
```

and it will start the instance up. Once the instance is running we can ssh into it with:

```sh
just vast-ssh
```

And if we want to stop it we can do so with:

```sh
just vast-stop 46810398
```

### Using the DevBox
Now that we have a development box provisioned and running we would like to have a workflow that allows us to go from code change to compilation and test in as little time as possible. To do this we have the following two commands at our disposal:
```sh
just watch-vast-rsync # sync to remote on file change
just watch-inf-test # recompile and test on file change
```

One terminal we have a synchronisation loop and in the other we have the compilation and test loop (should run after ssh). I would like these two to initialize automatically after we provision with `just vast start {{id}}` but for now it is fine.

### What is this DevBox
Now what is this container that we use for development? Well this container (no surprises here) is also built using nix. Starting from the `nixos/nix` base image I inherit `cuda-oxide`'s build inputs and native build inputs to make sure I have all the build dependencies baked in the container. With that ready I just have a sshd server started with my personal public ssh key.

### Inputs to hold everything down
Now our flake takes as inputs `cuda-oxide` which is the nice part as it lets us make sure versions and dependencies line up, and don't move. For example the current pinned revision, as of writing this post, has `cuda-oxide` only compatible with CUDA 13.X which means I need to take that into account.
```nix
inputs = {
  cuda-oxide.url = "github:NVlabs/cuda-rust?dir=cuda-oxide";
  nixpkgs.follows = "cuda-oxide/nixpkgs";

  # Host-only source for the Vast CLI, which is not yet packaged by the
  # nixpkgs revision pinned by cuda-oxide.
  vast-nixpkgs.url = "github:NixOS/nixpkgs/7a0f122f5090cf4c2ade2a13a0e229d4e19ba71f";
};
```
The other nice thing of taking `cuda-oxide` as an input is that we can follow the version of `nixpkgs` they are using. This means that not only we have the same versions of cuda but also of every single other package in `nixpkgs`, from `emacs` to `sshd`. If they install a package through `nixpkgs` I can install it to and ensure I have the same exact version, to the hash level.

# Start of the project
As I said this is only the start but it has already got me excited, I can have a development box ready to use in less than 5 minutes and compile a new kernel in less than 10. The aim is to keep bringing that number down by automating more and more, but this is a good start. By far the best thing of this setup is the deterministic nature. I feel completely at peace that no matter when I provision another box (be tomorrow or in 5 years) it will "just work".
