import subprocess
import time
import logging
from logging.handlers import RotatingFileHandler

# IPMI settings
IPMI_HOST = "192.168.1.70"
IPMI_USER = "root"
IPMI_PASS = "calvin"

# Fan speed thresholds (CPU)
CPU_MIN_TEMP = 35
CPU_MAX_TEMP = 55
CPU_MIN_FAN = 10  # Minimum fan speed in decimal
CPU_MAX_FAN = 100  # Maximum fan speed in decimal

# Fan speed thresholds (GPU)
GPU_MIN_TEMP = 45
GPU_MAX_TEMP = 70
GPU_MIN_FAN = 10  # Minimum fan speed in decimal
GPU_MAX_FAN = 100  # Maximum fan speed in decimal

# Refresh interval (seconds)
REFRESH_INTERVAL = 20

# Set up logging
LOG_FILE_PATH = "/opt/fan_control/fan_control.log"
logger = logging.getLogger('FanControlLogger')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10000, backupCount=1)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def run_ipmi_command(command: str) -> None:
    """Run an IPMI command using subprocess and log the result."""
    try:
        output = subprocess.check_output(command, shell=True)
        logger.info(f"Running command: {command} | Output: {output.decode()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running command: {e}")

def get_temperatures(sensor_command: str) -> dict:
    """Run a sensor command to retrieve temperature data and return the result."""
    try:
        output = subprocess.check_output(sensor_command, shell=True)
        temperatures = {}
        for line in output.decode().splitlines:
            if ":" in line:
                _, value = line.strip().split(":")
                temperatures[value.split()[0]] = int(value.split()[-1])
        return temperatures
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting temperatures: {e}")
        return {}

def calculate_fan_speed(temperature: int, min_temp: int, max_temp: int, min_fan: int, max_fan: int) -> int:
    """Calculate the fan speed based on the input temperature."""
    if temperature < min_temp:
        return min_fan
    elif temperature > max_temp:
        return max_fan
    else:
        return min(int(((temperature - min_temp) / (max_temp - min_temp)) * (max_fan - min_fan) + min_fan), max_fan)

def main() -> None:
    """Main loop of the program."""
    while True:
        gpu_temperatures = get_temperatures("nvidia-smi")
        cpu_temperature = int(subprocess.check_output(["sensors"], shell=True).decode().splitlines[-1].split(":")[1].split()[0])
        gpu_fan_speed = calculate_fan_speed(gpu_temperatures.get("GPU", 0), GPU_MIN_TEMP, GPU_MAX_TEMP, GPU_MIN_FAN, GPU_MAX_FAN)
        cpu_fan_speed = calculate_fan_speed(cpu_temperature, CPU_MIN_TEMP, CPU_MAX_TEMP, CPU_MIN_FAN, CPU_MAX_FAN)

        command = f"ipmi set fan {gpu_fan_speed} on"
        run_ipmi_command(command)

        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
