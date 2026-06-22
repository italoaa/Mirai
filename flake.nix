{
  description = "Astro website with Nix dev shell, Codex, and static build";

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
            export NPM_CONFIG_PREFIX="$PWD/.npm-global"
            export NPM_CONFIG_CACHE="$PWD/.npm-cache"
            export PATH="$NPM_CONFIG_PREFIX/bin:$PATH"

            mkdir -p "$NPM_CONFIG_PREFIX" "$NPM_CONFIG_CACHE"

            echo "Astro dev shell"
            echo "node:  $(node --version)"
            echo "npm:   $(npm --version)"

            echo ""
            echo "Run Astro:"
            echo "  npm run dev"
            echo ""
            echo "Build with Nix:"
            echo "  nix build"
          '';
        };

        packages.default = pkgs.buildNpmPackage {
          pname = "mirai";
          version = "0.1.0";

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
      }
    );
}
