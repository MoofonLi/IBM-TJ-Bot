# Follow the steps below to run in first time:
### Handbook
https://illustrious-soup-639.notion.site/AI-challenger-camp-HUB-1ed3de23d5a580f5b403f8b53a614e8a
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
        renderer: networkd
        wlan0:
            access-points:
                Original Wifi:
                    password: 3499433eb6938b425aca017d84c9636a9964710fe2ca45ef0>
                "New Wifi":
                    password: <pw>
            dhcp4: true
            optional: true
```
```
sudo netplan apply
```
### Install system dependencies
```
sudo apt update
```
```
sudo apt upgrade
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
chmod +x install_dependencies.sh start_tjbot.sh
```
```
./install_dependencies.sh
```
```
source ~/.bashrc
```
```
./start_tjbot.sh
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
## ERROR
### host key change
```
ssh-keygen -R 192.168.8.108
```
### 清理 streamlit 進程
```
ps aux | grep streamlit
```
```
sudo kill -TERM <PID>
```

### Git Pull (本地與遠端變更衝突)
```
git checkout -- start_tjbot.sh && git pull origin main
```