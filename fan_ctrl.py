import subprocess
import os
import time

# IPMI settings
IPMI_HOST = "192.168.1.70"
IPMI_USER = "root"
IPMI_PASS = "calvin"

# Fan speed thresholds (CPU and GPU)
CPU_MIN_TEMP = 35
CPU_MAX_TEMP = 50
CPU_MIN_FAN = 15
CPU_MAX_FAN = 100

GPU_MIN_TEMP = 45
GPU_MAX_TEMP = 65
GPU_MIN_FAN = 15
GPU_MAX_FAN = 100

# Refresh interval (seconds)
REFRESH_INTERVAL = 10

def run_ipmitool_command(command):
    subprocess.run(command, shell=True)

def get_cpu_temperature():
    try:
        result = subprocess.run(['sensors', '-u'], capture_output=True, text=True)
        output = result.stdout
        cpu_temp_line = next(line for line in output.splitlines() if "temp1_input" in line)
        return float(cpu_temp_line.split()[1])
    except Exception as e:
        print(f"Error reading CPU temperature: {e}")
        return 0

def get_gpu_temperatures():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,nohe>
        output = result.stdout
        return [int(temp.strip()) for temp in output.splitlines()]
    except Exception as e:
        print(f"Error reading GPU temperatures: {e}")
        return []

def set_fan_speed(fan_speed_hex):
    fan_speed_hex = fan_speed_hex[2:]  # Remove the "0x" prefix
    os.system(f"ipmitool -I lanplus -H {IPMI_HOST} -U {IPMI_USER} -P {IPMI_PASS} raw 0x30 0x30 0>

def main():
    # Run the ipmitool command to initialize settings on script start
    init_command = "ipmitool -I lanplus -H 192.168.1.70 -U root -P calvin raw 0x30 0x30 0x01 0x0>
    run_ipmitool_command(init_command)

    while True:
        cpu_temp = get_cpu_temperature()
        gpu_temperatures = get_gpu_temperatures()

        # Adjust CPU fan speed
        if CPU_MIN_TEMP <= cpu_temp < CPU_MAX_TEMP:
            cpu_fan_speed = int((cpu_temp - CPU_MIN_TEMP) / (CPU_MAX_TEMP - CPU_MIN_TEMP) * (CPU>
            set_fan_speed(hex(cpu_fan_speed))

        # Adjust GPU fan speed
        if GPU_MIN_TEMP <= max(gpu_temperatures) < GPU_MAX_TEMP:
            gpu_fan_speed = int((max(gpu_temperatures) - GPU_MIN_TEMP) / (GPU_MAX_TEMP - GPU_MIN>
            set_fan_speed(hex(gpu_fan_speed))

        time.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    main()
