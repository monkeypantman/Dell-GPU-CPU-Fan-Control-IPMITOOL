# rename this file to fan_control.py if in use
# this script includes a 5% over the last 3 calcualtion varience. Anything within that varience is ignored. This creates less ipmitool requests and a more stable fan speed - which is less annoying. 
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
    # Initialize a list to store the last three fan speeds
    last_three_fan_speeds = []

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
        
        # Check if we have at least three previous fan speeds to compare
        if len(last_three_fan_speeds) >= 3:
            # Calculate the average of the last three fan speeds
            avg_last_three_fan_speed = sum(last_three_fan_speeds[-3:]) / 3
            # Calculate the difference in percentage
            diff_percentage = abs(fan_speed - avg_last_three_fan_speed) / avg_last_three_fan_speed * 100

            # If the difference is more than 5%, send the ipmitool command
            if diff_percentage > 5:
                fan_speed_hex = format(fan_speed, '02x').upper()  # Convert to uppercase hexadecimal
                command = f"ipmitool -I lanplus -H {IPMI_HOST} -U {IPMI_USER} -P {IPMI_PASS} raw 0x30 0x30 0x02 0xff 0x{fan_speed_hex}"
                run_ipmitool_command(command)
        else:
            # If we don't have enough data points, send the command anyway
            fan_speed_hex = format(fan_speed, '02x').upper()
            command = f"ipmitool -I lanplus -H {IPMI_HOST} -U {IPMI_USER} -P {IPMI_PASS} raw 0x30 0x30 0x02 0xff 0x{fan_speed_hex}"
            run_ipmitool_command(command)

        # Update the list of last three fan speeds
        last_three_fan_speeds.append(fan_speed)
        # Ensure only the last three readings are kept
        last_three_fan_speeds = last_three_fan_speeds[-3:]

        time.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    main()
