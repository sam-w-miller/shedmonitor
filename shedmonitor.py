# Code to read sensor information from Enviro Hat and save as a CSV

# Import configparser to read values from config file
import configparser

# Import libraries connected to the Enviro Hat
# Library for temperature/pressure/humidity sensor
from bme280 import BME280
try:
	from smbus2 import SMBus
except ImportError:
	from smbus import SMBus
# Library for light and proximity sensor
try:
	from ltr559 import LTR559
	ltr559 = LTR559()
except ImportError:
	import ltr559

# Import os so that we can store results in a directory
import os

# Import time so that we can store the current time along with the sensor data
import time

# Import pathlib so that we can check for the directory and file existence
import pathlib

# Import logging so that we can identify errors
import logging

# Initialise the logging process
logger = logging.getLogger(__name__)
logging.basicConfig(filename="shedmonitor.log", encoding="utf-8", format="%(asctime)s %(message)s", level=logging.DEBUG)
logger.debug("Starting shedmonitor.py")

# Read config file
config = configparser.ConfigParser()
config.read("params.config")
data_dir = config["Data_Location"]["directory"]

# Initialise sensors
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

# Initialise variables that will hold data from the sensors
temperature = 0
pressure = 0
humidity = 0
lux = 0
prox = 0

logger.debug("Attempting to read sensors")

# As the first reading from the sensors seems to be low, loop to get the second reading
i = 0
while i < 2:
	temperature = bme280.get_temperature()
	pressure = bme280.get_pressure()
	humidity = bme280.get_humidity()
	lux = ltr559.get_lux()
	prox = ltr559.get_proximity()
	i = i + 1
	# Add a pause in the loop - seems to improve the accuracy of the reading
	time.sleep(1)

# Get the current date time for logging purposes and filename
current_date = time.strftime("%Y-%m-%d")
current_time = time.strftime("%Y-%m-%d %H:%M:%S")

logger.debug("Checking for directory")
# Check to see if we have the directory to store the data files
if not os.path.exists(data_dir):
	os.makedirs(data_dir)

# Get the path to the data directory
current_directory = pathlib.Path(__file__).parent.resolve()
sub_directory_path = current_directory / data_dir

# Build file name
file_name = current_date + ".csv"

# Create full path
file_path = os.path.join(sub_directory_path, file_name)

# Check to see if file already exists and create if it doesn't
check_file = os.path.exists(file_path)
if not(check_file):
	# Need to create file for the current day
	f = open(file_path, "w+")
	# Add a header row
	f.write("datetime,temperature,pressure,humidity,light,proximity\n")
	f.close

logger.debug("Writing data")
# Append the data to the file
with open(file_path, "a") as f:
	f.write(current_time + "," + str(temperature) + "," + str(pressure) + "," + str(humidity) + "," + str(lux) + "," + str(prox) + "\n")
	f.close
