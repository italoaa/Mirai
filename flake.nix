{
  description = "Simple Astro website with a Nix dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        nodejs = pkgs.nodejs_24;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            nodejs
            pkgs.git
          ];

          shellHook = ''
            echo "Astro dev shell"
            echo "node: $(node --version)"
            echo "npm:  $(npm --version)"
            echo ""
            echo "Run: npm create astro@latest ."
            echo "Then: npm run dev"
          '';
        };
      }
    );
}
