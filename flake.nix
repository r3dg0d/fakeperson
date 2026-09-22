{
  description = "fakeperson — photorealistic fictional people CLI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python313;
        fakeperson = python.pkgs.buildPythonApplication {
          pname = "fakeperson";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";
          nativeBuildInputs = with python.pkgs; [ hatchling ];
          propagatedBuildInputs = with python.pkgs; [ click pillow ];
          meta = with pkgs.lib; {
            description = "Photorealistic fictional people CLI";
            license = licenses.mit;
            mainProgram = "fakeperson";
          };
        };
      in {
        packages.default = fakeperson;
        packages.fakeperson = fakeperson;
        apps.default = flake-utils.lib.mkApp { drv = fakeperson; };
        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            python.pkgs.pip
            python.pkgs.click
            python.pkgs.pillow
            python.pkgs.pytest
          ];
        };
      });
}
