import subprocess
import os
import time
import socket
import logging
from logging.handlers import RotatingFileHandler

# IPMI settings
IPMI_HOST = "192.168.1.70"
IPMI_USER = "root"
IPMI_PASS = "calvin"

# Fan speed thresholds (CPU)
CPU_MIN_TEMP = 35
CPU_MAX_TEMP = 50
CPU_MIN_FAN = 0
CPU_MAX_FAN = 64

# Fan speed thresholds (GPU)
GPU_MIN_TEMP = 45
GPU_MAX_TEMP = 65
GPU_MIN_FAN = 0
GPU_MAX_FAN = 64

# Refresh interval (seconds)
REFRESH_INTERVAL = 10

# Set up logging
log_file_path = "/opt/fan_control/fan_control.log"
logger = logging.getLogger('FanControlLogger')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=10)
logger.addHandler(handler)

def get_hostname(ip_address):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except socket.herror:
        return None

def run_ipmitool_command(command):
    try:
        subprocess.run(command, shell=True)
        logger.info(f"Command executed: {command}")
    except Exception as e:
        logger.error(f"Error executing command: {e}")

def get_cpu_temperature():
    try:
        result = subprocess.run(['sensors', '-u'], capture_output=True, text=True)
        output = result.stdout
        core_temp_lines = [line for line in output.splitlines() if "Core" in line and "_input" in line]
        core_temps = [float(line.split()[1]) for line in core_temp_lines]
        avg_cpu_temp = sum(core_temps) / len(core_temps) if core_temps else 0
        return avg_cpu_temp
    except Exception as e:
        logger.error(f"Error reading CPU temperature: {e}")
        return 0

def get_gpu_temperatures():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'], capture_output=True, text=True)
        output = result.stdout
        return [int(temp.strip()) for temp in output.splitlines()]
    except Exception as e:
        logger.error(f"Error reading GPU temperatures: {e}")
        return []

def set_fan_speed(fan_speed):
    if not (0 <= fan_speed <= 60):
        logger.error(f"Invalid fan speed value ({fan_speed}). Must be between 0 and 60.")
        return

    # Convert to hex and remove the "0x" prefix
    fan_speed_hex = hex(fan_speed)[2:] if fan_speed > 15 else '0' + hex(fan_speed)[2:]
    command = f"ipmitool -I lanplus -H {IPMI_HOST} -U {IPMI_USER} -P {IPMI_PASS} raw 0x30 0x30 0x02 0xff {fan_speed_hex}"
    run_ipmitool_command(command)

def main():
    hostname = get_hostname(IPMI_HOST)
    if hostname:
        logger.info(f"Hostname for {IPMI_HOST}: {hostname}")
    else:
        logger.error(f"Unable to resolve hostname for {IPMI_HOST}")
        return  # Exit the script if the hostname cannot be resolved

    init_command = f"ipmitool -I lanplus -H {IPMI_HOST} -U {IPMI_USER} -P {IPMI_PASS} raw 0x30 0x30 0x01 0x00"
    run_ipmitool_command(init_command)

    while True:
        cpu_temp = get_cpu_temperature()
        gpu_temperatures = get_gpu_temperatures()

        if CPU_MIN_TEMP <= cpu_temp < CPU_MAX_TEMP:
            cpu_fan_speed = int((cpu_temp - CPU_MIN_TEMP) / (CPU_MAX_TEMP - CPU_MIN_TEMP) * (CPU_MAX_FAN - CPU_MIN_FAN) + CPU_MIN_FAN)
            set_fan_speed(cpu_fan_speed)

        if gpu_temperatures and GPU_MIN_TEMP <= max(gpu_temperatures) < GPU_MAX_TEMP:
            gpu_fan_speed = int((max(gpu_temperatures) - GPU_MIN_TEMP) / (GPU_MAX_TEMP - GPU_MIN_TEMP) * (GPU_MAX_FAN - GPU_MIN_FAN) + GPU_MIN_FAN)
            set_fan_speed(gpu_fan_speed)

        time.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    main()
