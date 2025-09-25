# Code to read sensor information from Enviro Hat and save as a CSV

import configparser
import logging
from pathlib import Path
import time
import sys

# Try to import sensor libraries
try:
    from bme280 import BME280
except ImportError as e:
    print("Could not import bme280:", e)
    sys.exit(1)

try:
    from smbus2 import SMBus
except ImportError:
    try:
        from smbus import SMBus
    except ImportError as e:
        print("Could not import smbus/smbus2:", e)
        sys.exit(1)

try:
    from ltr559 import LTR559
except ImportError as e:
    print("Could not import ltr559:", e)
    sys.exit(1)

# Read config file
config = configparser.ConfigParser()
config.read("params.config")
data_dir = config.get("Data_Location", "directory", fallback="data")
log_file = config.get("Logging", "logfile", fallback="shedmonitor.log")
sensor_sleep = config.getfloat("Sensor", "sleep", fallback=1.0)

# Setup logging
logging.basicConfig(filename=log_file, encoding="utf-8",
                    format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Starting shedmonitor.py")

def read_sensors(bme280, ltr559, retries=2, delay=1.0):
    """Read sensors, taking multiple readings for accuracy."""
    temperature = pressure = humidity = lux = prox = None
    for _ in range(retries):
        try:
            temperature = bme280.get_temperature()
            pressure = bme280.get_pressure()
            humidity = bme280.get_humidity()
            lux = ltr559.get_lux()
            prox = ltr559.get_proximity()
        except Exception as e:
            logger.error(f"Sensor read failed: {e}")
            raise
        time.sleep(delay)
    return temperature, pressure, humidity, lux, prox

def ensure_directory(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
        logger.debug(f"Created directory: {path}")

def ensure_daily_file(file_path: Path):
    if not file_path.exists():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("datetime,temperature,pressure,humidity,light,proximity\n")
        logger.debug(f"Created new daily data file: {file_path}")

def write_data(file_path: Path, row: str):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(row + "\n")
        logger.debug(f"Wrote data row: {row}")
    except Exception as e:
        logger.error(f"Failed to write data to {file_path}: {e}")

def main():
    # Initialise sensors
    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)
    ltr559 = LTR559()

    logger.debug("Attempting to read sensors")
    try:
        temperature, pressure, humidity, lux, prox = read_sensors(
            bme280, ltr559, retries=2, delay=sensor_sleep
        )
    except Exception:
        logger.error("Aborting due to sensor error.")
        return

    # Prepare paths
    current_date = time.strftime("%Y-%m-%d")
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    script_dir = Path(__file__).parent.resolve()
    sub_directory_path = script_dir / data_dir
    ensure_directory(sub_directory_path)

    file_path = sub_directory_path / f"{current_date}.csv"
    ensure_daily_file(file_path)

    # Write data row
    row = f"{current_time},{temperature},{pressure},{humidity},{lux},{prox}"
    write_data(file_path, row)

if __name__ == "__main__":
    main()