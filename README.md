# dell_GPU_CPU_Fan_Control
A python script to control the Poweredge fans through IPMItool based on GPU and CPU temperatures


There are a few prerequisites for this. 
sudp apt update 

#1. IMPItool needs to be installed.
sudo apt install ipmitool

#2. sensors needs to be installed
sudo apt install lm-sensors

#3. NVIDIA drivers installed and the output of nvidia-smi to give driver and card information
watch -n 0.5 nvidia-smi

#4. Python installed
sudo apt install python3

#Once all this is installed, take the fan_ctrl.py file and store it in /opt/fan_control
mkdir /opt/fan_control
cd /opt/fan_ctrl
wget https://github.com/monkeypantman/dell_GPU_CPU_Fan_Control/blob/main/fan_ctrl.py

#Then move to the services folder  
cd /etc/systemd/system

#get the service file fan_ctrl.service
wget https://github.com/monkeypantman/dell_GPU_CPU_Fan_Control/blob/main/fan_ctrl.service

#Enable the service and start then check the status
systemctl daemon-reload
systemctl enable fan_ctrl.service
systemctl start fan_ctrl.service
systemctl status fan_ctrl.service
