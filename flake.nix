{
  description = "Dev environment with Terraform, Google Cloud SDK, and jq, pinned to NixOS 23.05";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.05";
    # gives us the last open source version, 1.5.7
    nixpkgsForTF.url="github:NixOS/nixpkgs?rev=39ed4b64ba5929e8e9221d06b719a758915e619b";
  };

  outputs = { self, nixpkgs,nixpkgsForTF, ... }:
    let
      systems = [ "x86_64-linux" ];
      terraform = nixpkgsForTF.legacyPackages.x86_64-linux.terraform.overrideAttrs (oldAttrs: {
        # disable tests which take forever
        doCheck = false;
      });
    in
    {
      supportedSystems = systems;

      devShell.x86_64-linux = let
        pkgs = nixpkgs.legacyPackages.x86_64-linux;
      in
      pkgs.mkShell {
        packages = [
          terraform
          (pkgs.google-cloud-sdk.withExtraComponents[
            pkgs.google-cloud-sdk.components.gke-gcloud-auth-plugin
            pkgs.google-cloud-sdk.components.kubectl
          ])
          pkgs.jq
        ];
        shell = pkgs.bashInteractive;
      };
    };
}