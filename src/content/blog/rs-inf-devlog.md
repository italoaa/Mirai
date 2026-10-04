---
title: "Devlog 1: Introduction to Rs-inf"
description: "Building an inference engine in rust with cuda-oxide."
pubDate: "2026-10-04"
tags: ["Nix", "Rust", "Cuda"]
draft: true
---

The project is being developed at: [rs-inf github](https://github.com/italoaa/rs-inf)

# What is Rs-inf
Like the name suggest is a simple inference engine with rust. The kicker of this project is the use of the [cuda-oxide](https://github.com/NVIDIA/cuda-rust/tree/main/cuda-oxide) crate, which is quite new, and it allows you to write CUDA (SIMT) kernels but in pure rust. This project will also help me stay updated with what is going on with cuda-oxide; there are lots of interesting things coming like using lean to prove kernels.

The initial objective for this project, at least as of writing this post, is to be able to run a Qwen3 dense model. That is it. Even though this might sound unambitious I think it really is. If we take into consideration that: I have very little experience with cuda, will not use any coding agent (after all this is mostly to learn) and I am not fully updated with the latest LLM model architectures I think this is a good initial goal to set. Later I can think of optimizing the kernels or implementing more general operations that allow me to run MoEs or other model families.

# The development environment
So these are great plans but there is a problem: I do not have a nvidia GPU. My solution, use [vast.ai](https://vast.ai) to temporarily rent development boxes with access to nvidia GPUs. Now I know what you are thinking: Remote development? That sounds like a pain. Here comes **NIX** to the rescue.

Currently I have implemented a development workflow that I am happy with, it still needs a lot of work but right now I can develop in my host machine and upon file change in less than a couple seconds the code is already compiling in the development box.

Most of my first week was spent on getting this setup to a place where I can start working with the GPU and not have many problems (it still a work in progress).

## Deterministic Environment
I can't stress enough the importance of having a deterministic environment that is the same no matter **when** and **where** it runs. I think in a project like this where we need to juggle all of the following:
1. Host Cuda driver
2. Cuda Toolkit
3. cuda-oxide compatibility
4. dynamic linking paths
5. Hardware compatibility

And keep them all aligned ... that is why we need nix, later I will dive deeper.

### DevShells and provisioning the DevBox
Now one of the nice features of nix is the development shells. In the projects flake I built a devShell for `darwin` and for `linux`. In the case of `darwin`, I spin up a docker container based on `nixos/nix` image (also pinned) then inside that container I start the `linux` dev shell. This shell inherits `cuda-oxide`'s startup hook so it handles all the checking of dependencies and making sure everything is aligned.

Furthermore, the project has a `secrets.env` that holds the api key to vast. This file is encrypted using sops (of course) and during the startup of the dev shell we decrypt and load the secrets to the environment. With the secrets loaded we can make a request to vast to list all the available GPUs for us to use.

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

And if we will to stop it we can do so with:

```sh
just vast-stop 46810398
```

### Using the DevBox
Now that we have a development box provisioned and running we would like to have a workflow that allows us to go from code change to compilation and test in as little time as possible. To do this we have the following two commands at our disposal:
```sh
just watch-vast-rsync # sync to remote on file change
just watch-inf-test # recompile and test on file change
```

The idea of the setup is to have in one terminal the synchronisation loop that pushes our changes to the remote, and in another terminal after we have done a `just vast-ssh` from inside the machine we can have the compilation and test loop.

### What is this DevBox
- in here introduce the container output of the flake that builds the container
- then lead the point to the place where it is rational to think, so where do we define the versions of the things getting installed to the container
- this will make the next paragraph flow naturally out of necessity.
- this means that my container already has most of my dependencies already bundled with it and there is no version mismatch that will secretly make me waste time.
- I only need to ssh into the box, cd into the project and run the `just watch-inf-test` and it does it all.

### Inputs to hold everything down
First we must pin what version of what we are going to use. In the case of our `flake.nix` we have the following:
```nix
inputs = {
  cuda-oxide.url = "github:NVlabs/cuda-rust?dir=cuda-oxide";
  nixpkgs.follows = "cuda-oxide/nixpkgs";

  # Host-only source for the Vast CLI, which is not yet packaged by the
  # nixpkgs revision pinned by cuda-oxide.
  vast-nixpkgs.url = "github:NixOS/nixpkgs/7a0f122f5090cf4c2ade2a13a0e229d4e19ba71f";
};
```
In our `flake.lock` we have the exact version that the cuda-oxide project uses for their own dependencies in their own `flake.nix`. This means that when we specify `nixpkgs` to follow that input we are saying to make sure we are in sync.

- now say how with this and just i can search for only boxes with cuda 13.X and that I could even go further and try to only use newer architectures where the SM's are newer and compatible with the 13.x stuff.
- then mention how with


### Improvements
- make the watch compilation-test loop start automatically on container start
- start the rsync command automatically once a box is provisioned to vast
- add a exit trap to the devshell that will make sure the user has no more running vast instances (no wasting resources)
