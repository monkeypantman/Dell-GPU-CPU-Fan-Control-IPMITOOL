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
log_file_path = "/opt/fan_control/fan_control.log"
logger = logging.getLogger('FanControlLogger')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=1)
logger.addHandler(handler)

def run_ipmitool_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(f"Command executed: {command}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e}")

def get_temperatures(sensor_command):
    try:
        result = subprocess.run(sensor_command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error reading temperatures: {e}")
        return ""

def calculate_fan_speed(temp, min_temp, max_temp, min_fan, max_fan):
    if temp <= min_temp:
        return min_fan
    elif temp >= max_temp:
        return max_fan
    else:
        return int((temp - min_temp) / (max_temp - min_temp) * (max_fan - min_fan) + min_fan)

def main():
    while True:
        # Get GPU temperature
        gpu_temp_output = get_temperatures(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'])
        gpu_temps = [int(temp.strip()) for temp in gpu_temp_output.splitlines() if temp.strip().isdigit()]
        gpu_fan_speed = calculate_fan_speed(max(gpu_temps), GPU_MIN_TEMP, GPU_MAX_TEMP, GPU_MIN_FAN, GPU_MAX_FAN)

        # Get CPU temperature
        cpu_temp_output = get_temperatures(['sensors', '-u'])
        core_temp_lines = [line for line in cpu_temp_output.splitlines() if "Core" in line and "_input" in line]
        core_temps = [float(line.split()[1]) for line in core_temp_lines]

        if core_temps:
            avg_cpu_temp = sum(core_temps) / len(core_temps)
            cpu_fan_speed = calculate_fan_speed(avg_cpu_temp, CPU_MIN_TEMP, CPU_MAX_TEMP, CPU_MIN_FAN, CPU_MAX_FAN)
        else:
            cpu_fan_speed = CPU_MIN_FAN

        # Set fan speed
        fan_speed = max(gpu_fan_speed, cpu_fan_speed)
        fan_speed_hex = format(fan_speed, '02x').upper()  # Convert to uppercase hexadecimal
        command = f"ipmitool -I lanplus -H {IPMI_HOST} -U {IPMI_USER} -P {IPMI_PASS} raw 0x30 0x30 0x02 0xff 0x{fan_speed_hex}"
        run_ipmitool_command(command)

        time.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    main()
