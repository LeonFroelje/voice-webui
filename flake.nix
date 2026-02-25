{
  description = "Voice Assistant WebUI Package";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    nixvim = {
      url = "github:nix-community/nixvim";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nixvimModules = {
      url = "github:LeonFroelje/nixvim-modules";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      nixvim,
      nixvimModules,
    }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      # --- 1. The Frontend Build ---
      # This builds the Svelte project into a static 'dist' folder
      frontend = pkgs.buildNpmPackage {
        pname = "voice-assistant-frontend";
        version = "1.0.0";
        src = ./frontend; # Points to your frontend subdir
        npmDepsHash = "sha256-xYk4y/bwnbcZEnTao31nxN386/KhqsUfVZrwVaUdmEE="; # Run 'nix build' and paste the hash here after it fails
        installPhase = ''
          cp -r dist $out
        '';
      };

      # --- 2. The Python Backend ---
      # This builds the FastAPI app and includes the frontend assets
      backend = pkgs.python314.pkgs.buildPythonApplication {
        pname = "voice-webui-backend";
        version = "1.0.0";
        src = ./backend; # Points to your backend subdir

        propagatedBuildInputs = with pkgs.python314Packages; [
          pydantic
          boto3
          aiosqlite
          aiomqtt
          pydantic-settings
          python-dotenv
          websockets
          fastapi
          psutil
          python-multipart
          setuptools
          setuptools-scm
          uvicorn
        ];
        pyproject = true;

        # Tell the app where the frontend files are via an Environment Variable
        makeWrapperArgs = [
          "--set FRONTEND_DIST_PATH ${frontend}"
          "--set ENVIRONMENT PROD"
        ];

        # Assuming your entry point is main.py
        # installPhase = ''
        #   mkdir -p $out/bin $out/lib
        #   cp -r . $out/lib/
        #   makeWrapper ${pkgs.python314}/bin/python $out/bin/voice-assistant \
        #     --add-flags "$out/lib/main.py" \
        #     ''${makeWrapperArgs[@]}
        # '';
      };

    in
    {
      # --- THE PACKAGE ---
      packages.${system}.default = backend;
      nixosModules.default =
        {
          self,
          config,
          lib,
          pkgs,
          ...
        }:

        let
          cfg = config.services.voiceWebUI;
          inherit (lib)
            mkEnableOption
            mkOption
            mkIf
            types
            ;
        in
        {
          options.services.voiceWebUI = {
            enable = mkEnableOption "Voice Assistant Web Dashboard";

            package = mkOption {
              type = types.package;
              default = self.packages.${pkgs.system}.default;
              description = "The voice-webui package to use.";
            };

            environmentFile = mkOption {
              type = types.nullOr types.path;
              default = null;
              example = "/run/secrets/voice-webui.env";
              description = ''
                Path to an environment file containing secrets.
                Should contain: S3_SECRET_KEY=your-secret
              '';
            };

            settings = {
              host = mkOption {
                type = types.str;
                default = "0.0.0.0";
                description = "IP address to bind the FastAPI server to.";
              };
              port = mkOption {
                type = types.int;
                default = 8000;
                description = "Port for the FastAPI server.";
              };
              mqttHost = mkOption {
                type = types.str;
                default = "localhost";
                description = "Mosquitto broker IP/Hostname.";
              };
              mqttPort = mkOption {
                type = types.int;
                default = 1883;
                description = "Mosquitto broker port.";
              };
              s3Endpoint = mkOption {
                type = types.str;
                default = "http://localhost:3900";
                description = "URL to S3 storage.";
              };
              s3AccessKey = mkOption {
                type = types.nullOr types.str;
                default = "your-access-key";
                description = "S3 Access Key.";
              };
              s3Bucket = mkOption {
                type = types.str;
                default = "voice";
                description = "S3 Bucket Name.";
              };
              logLevel = mkOption {
                type = types.str;
                default = "INFO";
                description = "Logging Level (DEBUG, INFO, etc.).";
              };
            };
          };

          config = mkIf cfg.enable {
            systemd.services.voice-webui = {
              description = "Voice Assistant Web Management Dashboard";
              wantedBy = [ "multi-user.target" ];
              after = [ "network.target" ];

              serviceConfig = {
                # The package entrypoint we defined in pyproject.toml
                ExecStart = "${cfg.package}/bin/voice-webui";

                # Secrets
                EnvironmentFile = mkIf (cfg.environmentFile != null) cfg.environmentFile;

                # Systemd hardening
                DynamicUser = true;
                ProtectSystem = "strict";
                ProtectHome = true;
                PrivateTmp = true;

                # This creates /var/lib/voice-webui/ and sets it as the working directory
                StateDirectory = "voice-webui";
                WorkingDirectory = "/var/lib/voice-webui";
              };

              # Mapping Nix options to the environment variables Pydantic expects
              environment = {
                WEB_HOST = cfg.settings.host;
                WEB_PORT = toString cfg.settings.port;

                MQTT_HOST = cfg.settings.mqttHost;
                MQTT_PORT = toString cfg.settings.mqttPort;

                S3_ENDPOINT = cfg.settings.s3Endpoint;
                S3_ACCESS_KEY = cfg.settings.s3AccessKey;
                S3_BUCKET = cfg.settings.s3Bucket;

                LOG_LEVEL = cfg.settings.logLevel;
                ENVIRONMENT = "PROD";
                PYTHONUNBUFFERED = "1";
              };
            };
          };
        };
      devShells.${system} = {
        default = pkgs.mkShell {
          name = "Python dev shell";
          packages = with pkgs; [

            fd
            ripgrep
            (nixvimModules.lib.mkNvim [
              nixvimModules.nixosModules.python
              nixvimModules.nixosModules.javascript
              nixvimModules.nixosModules.svelte
            ])
            (python314.withPackages (
              pypkgs: with pypkgs; [
                pydantic
                boto3
                aiosqlite
                aiomqtt
                pydantic-settings
                python-dotenv
                websockets
                fastapi
                psutil
                python-multipart
                uvicorn
              ]
            ))
            nodejs_22
          ];
          shellHook = "zsh";
        };

        uv =
          (pkgs.buildFHSEnv {
            name = "uv-shell";
            targetPkgs =
              p: with p; [
                uv
                zlib
                glib
                openssl
                stdenv.cc.cc.lib
                (nixvimModules.lib.mkNvim [
                  nixvimModules.nixosModules.python
                  nixvimModules.nixosModules.javascript
                  nixvimModules.nixosModules.svelte
                ])
              ];
            runScript = "zsh";

            multiPkgs = p: [
              p.zlib
              p.openssl
            ];
          }).env;
      };
    };
}
