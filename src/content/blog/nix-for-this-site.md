---
title: "Nix for this site"
description: "How I use Nix to build this site and provide a development environment."
pubDate: "2026-07-03"
tags: ["Nix", "AI"]
draft: false
---

# What is Nix with an example
I think the best way to describe nix is be drawing parallels to files like `package.json` or `requirements.txt`. These files are used to declare a "environment" where our code will run. This means packages, versions, dev and prod dependencies, etc.

For example take a look at the `flake.nix` for this project:
```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = # ...
        devShells.default = pkgs.mkShell {
          packages = [
            nodejs
            pkgs.git
          ];
        };

        packages.default = pkgs.buildNpmPackage {
          src = ./.;
          nodejs = nodejs;
          npmDepsHash = "sha256-OjRs5EVIORxkKg077FTwqV2M6sdvrSnth7dclBc5xik=";
          npmBuildScript = "build";
          installPhase = ''
            runHook preInstall
            mkdir -p $out
            cp -r dist/* $out/
            runHook postInstall
          '';
        };
  # ...
}
```

This seems like a lot to take in but you should think of it as a function. There are `inputs` and there are `outputs`. In the inputs we define the dependencies of our project, which in our case are `nixpkgs` and `flake-utils`.

For the outputs we expose two main things: `devShells` and `packages.default`. First `devShells` is a development environment where I develop the site. It has nodejs and git installed. This way when I type `nix develop` in the terminal, I will have a shell with nodejs and git available to me.

As for the `packages.default`, this is the actual build path for this site. We use a provided function called `buildNpmPackage` which will build our site, and then we install it in the `installPhase`, which copies the built files to the output path. 


# How to leverage Nix
Now with this defined, I have the **guarantee** from Nix that no matter what machine I run this on, I will have 1) the same environment to develop (no more it works on my machine) and 2) the same build output. And I leverage this with github workflows:
```yaml
# .github/workflows/pages.yml
# ...
      - name: Install Nix
        uses: DeterminateSystems/nix-installer-action@v17

      - name: Set up Nix cache
        uses: DeterminateSystems/magic-nix-cache-action@v13

      - name: Build site
        run: nix build
```

This workflow is interesting because it does not have any language specifics for building the site, thus it could be the same workflow even if I was using Python, Rust, etc. Not only do build artefacts will be cached but if it builds today it will build in the future. So I can be sure of maximum stability and if I am thinking of hosting this site for a long time (which I am) this initial effort will pay off in the long run.
