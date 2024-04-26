# Shed Monitor
This is a project that will use an Enviro Hat connected to a Raspberry PI to log the temperature, pressure, humidity, light and proximity in my shed locally on the device.

## Prerequisites
- A Raspberry Pi.
- A Pimoroni Enviro Hat - available [here](https://shop.pimoroni.com/products/enviro?variant=31155658489939).
- A cable connecting the Enviro Hat to the Pi like [this](https://shop.pimoroni.com/products/gpio-ribbon-cable-for-raspberry-pi-model-a-b-40-pins?variant=1005871341). *(I do not recommend putting the Enviro Hat straight into the Pi as it will affect temperature readings)*
- Installing the Enviro+ Python library on the Pi - see [here](https://learn.pimoroni.com/article/getting-started-with-enviro-plus).

## Libraries
- **configparser** to read parameters from the config file.
- **bme280**, **smbus** and **ltr559** to interface with the sensors from the Enviro Hat.
- **os** to create the data directory if required and the file to store results.
- **time** to create the timestamp for the log entry.
- **pathlib** to check for the the exists of the directory / file.
- **logging** to log information if needed.

## Program Files
- **params.config** holds the configuration parameters (nothing sensitive).
- **shedmonitor.py** is the program.
- **the data**, which will be written to the subdirectory in the config file. 

## High Level Code Flow
The program is broken down into these sections:
- Import all the libraries
- Read parameters and set up logging
- Initialise the sensors and the variables to store them
- Read the sensors (take the second reading as the first one seems to be lower)
- Create the file for the new day (if needed - should only be on the first execution of the day)
- Write to the file

## Scheduling
I recommend using cron to schedule this code to run at regular intervals. For example, the entry to run every 5 minutes would look like:

'\*/5 \* \* \* \* cd/\[folder where shedmonitor.py is stored\] && /usr/bin/python /\[folder where shedmonitor.py is stored\]/shedmonitor.py'  
