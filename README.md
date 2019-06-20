# PressureSensorRev
Craftbeerpi3 plugin to read a pressure sensor using the Adafruit ADS1115 Lib
Note: this is not a complete plugin for everyone as the units do not include non-US based measurements. This plugin is based on netanelbe's plugin (https://github.com/netanelbe/cbpi_pressure_sensor.git) and was created to solve my brewing solution.

Steps as follows:
1. Install and configure i2c (https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c)
2. Reboot!
3. Install and configure SPI (next page from step 11)
4. Reboot!
5. Install ADS1115 Lib (https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/ads1015-slash-ads1115?fbclid=IwAR2uf2wV0S_b-Akh0AnveEJYoFgGsLzXJd9FZn0r_0Ged0kr1ezEFlO-Czw)
