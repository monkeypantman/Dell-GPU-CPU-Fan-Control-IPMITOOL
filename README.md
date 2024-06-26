# Dell-GPU-CPU-Fan-Control-IPMITOOL
# A python script to control the Poweredge fans through IPMItool based on GPU and CPU temperatures

# This has been tested on a Dell PowerEdge R730 and R410. It should work on any Poweredge server that responds to ipmitool commands.

# Adjust the temperatures and fan control settings along with loop times in the fan_ctrl.py script.

# There are a few prerequisites for this. 
sudp apt update 

# 1. IMPItool needs to be installed.
sudo apt install ipmitool

# 2. sensors needs to be installed
sudo apt install lm-sensors

# 3. NVIDIA drivers installed and the output of nvidia-smi to give driver and card information
watch -n 0.5 nvidia-smi

# 4. Python installed
sudo apt install python3

# Once all this is installed, take the fan_ctrl.py file and store it in /opt/fan_control
mkdir /opt/fan_control
cd /opt/fan_ctrl
wget https://raw.githubusercontent.com/monkeypantman/Dell-GPU-CPU-Fan-Control-IPMITOOL/main/fan_ctrl.py
# make executable
sudo chmod +x fan_ctrl.py

# Then move to the services folder  
cd /etc/systemd/system

# get the service file fan_ctrl.service
wget https://raw.githubusercontent.com/monkeypantman/Dell-GPU-CPU-Fan-Control-IPMITOOL/main/fan_ctrl.service

#Enable the service and start then check the status
systemctl daemon-reload
systemctl enable fan_ctrl.service
systemctl start fan_ctrl.service
systemctl status fan_ctrl.service
