# Code to read sensor information from Enviro Hat and save as a CSV

import configparser
import logging
from pathlib import Path
import time
import sys

# Import display libraries
import st7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

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
font_header_size = config.getint("Display", "font_header_size", fallback=14)
font_text_size = config.getint("Display", "font_text_size", fallback=11)
text_colour_r = config.getint("Display", "text_colour_r", fallback=255)
text_colour_g = config.getint("Display", "text_colour_g", fallback=255)
text_colour_b = config.getint("Display", "text_colour_b", fallback=255)
back_colour_r = config.getint("Display", "back_colour_r", fallback=0)
back_colour_g = config.getint("Display", "back_colour_g", fallback=170)
back_colour_b = config.getint("Display", "back_colour_b", fallback=170)
text_start = config.getint("Display", "text_start", fallback=16)
text_gap = config.getint("Display", "text_gap", fallback=12)
label_x_position = config.getint("Display", "label_x_position", fallback=2)
value_x_position = config.getint("Display", "value_x_position", fallback=90)

# Setup logging
logging.basicConfig(filename=log_file, encoding="utf-8", format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Starting shedmonitor.py")

def read_sensors(bme280, ltr559, retries=2, delay=1.0):
	"""Read sensors, taking multiple readings for accuracy."""
	metrics = dict()
	for _ in range(retries):
		try:
			metrics.clear()
			metrics['Temperature'] = bme280.get_temperature()
			metrics['Pressure'] = bme280.get_pressure()
			metrics['Humidity'] = bme280.get_humidity()
			metrics['Light'] = ltr559.get_lux()
			metrics['Proximity'] = ltr559.get_proximity()
		except Exception as e:
			logger.error(f"Sensor read failed: {e}")
			raise
		time.sleep(delay)
	return metrics

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

def display_data(current_time, metrics):

	# Create LCD class instance.
	disp = st7735.ST7735(port=0, cs=1, dc="GPIO9", backlight="GPIO12", rotation=270, spi_speed_hz=10000000)
	# Initialize display.
	disp.begin()

	# Width and height to calculate text position.
	WIDTH = disp.width
	HEIGHT = disp.height

	# New canvas to draw on.
	img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
	draw = ImageDraw.Draw(img)

	# Create fonts and colours
	font_header = ImageFont.truetype(UserFont, font_header_size)
	font = ImageFont.truetype(UserFont, font_text_size)
	text_colour = (text_colour_r, text_colour_g, text_colour_b)
	back_colour = (back_colour_r, back_colour_g, back_colour_b)
	
	# Calculate position for the date text so that it appears in the center horizontally
	x1, y1, x2, y2 = font_header.getbbox(current_time)
	size_x = x2 - x1
	x = (WIDTH - size_x) / 2
	# The text will be 1 pixel from the top
	y = 1

	# Draw background rectangle and write text.
	draw.rectangle((0, 0, 160, 80), back_colour)
	draw.text((x, y), current_time, font=font_header, fill=text_colour)

	y_start = text_start

	# Iterate through the dictionary to display the metrics
	for x in metrics:
		draw.text((label_x_position, y_start), x + ":", font=font, fill=text_colour)
		draw.text((value_x_position, y_start), f'{metrics[x]:.3f}', font=font, fill=text_colour)
		y_start = y_start + text_gap

	# Send the image to the lcd
	disp.display(img)
	
def main():
	# Initialise sensors
	bus = SMBus(1)
	bme280 = BME280(i2c_dev=bus)
	ltr559 = LTR559()
	metrics = dict()

	logger.debug("Attempting to read sensors")
	try:
		metrics = read_sensors(bme280, ltr559, retries=2, delay=sensor_sleep)
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
	row = f"{current_time},{metrics['Temperature']},{metrics['Pressure']},{metrics['Humidity']},{metrics['Light']},{metrics['Proximity']}"
	write_data(file_path, row)

	# Display the data on the lcd screen
	display_data(current_time, metrics)

if __name__ == "__main__":
	main()