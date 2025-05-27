# Follow the steps below to run in first time:

### Network config and connection
```
ssh pi@your-ip-address
```
```
sudo nano /etc/netplan/50-cloud-init.yaml
```
```
network:
  version: 2
  wifis:
    wlan0:
      optional: true
      dhcp4: true
      access-points:
        "Example Wifi":
          auth:
            key-management: "psk"
            password: "Example Wifi"
        "New Wifi":
          auth:
            key-management: "psk"
            password: "New Password"
```
### Install system dependencies
```
sudo apt upgrade
```
```
sudo apt update
```
```
sudo apt install git -y
```
```
git clone https://github.com/MoofonLi/IBM-TJ-Bot
```
```
cd IBM-TJ-Bot
```
```
chmod +x install_dependencies.sh
```
```
./install_dependencies.sh
```
```
source ~/.bashrc
```
### Run application
```
cd IBM-TJ-Bot
```
```
chmod +x start_tjbot.sh
```
```
./start_tjbot.sh
```

# Follow the steps below to run after first run:
```
ssh pi@your-ip-address
```
```
./start_tjbot.sh
```