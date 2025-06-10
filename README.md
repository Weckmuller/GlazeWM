# GlazeWM

A project for running the GlazeWM window manager on Windows.


Config documentation

The default config file is generated at %userprofile%\.glzr\glazewm\config.yaml.

To use a different config file location, you can launch the GlazeWM executable with the CLI argument --config="...", like so:

./glazewm.exe start --config="C:\<PATH_TO_CONFIG>\config.yaml"

Or pass a value for the GLAZEWM_CONFIG_PATH environment variable:

setx GLAZEWM_CONFIG_PATH "C:\<PATH_TO_CONFIG>\config.yaml"
