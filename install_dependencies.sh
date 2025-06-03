#!/bin/bash

# 安裝系統依賴
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 python3-dev libffi-dev build-essential ffmpeg

# # 安裝 ngrok（如果還沒安裝）
# if ! command -v ngrok &> /dev/null; then
#     echo "Installing ngrok..."
#     # 下載 ngrok（ARM 版本適合樹莓派）
#     wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
#     sudo tar xzf ngrok-v3-stable-linux-arm.tgz -C /usr/local/bin
#     rm ngrok-v3-stable-linux-arm.tgz
# fi

echo "System dependencies installed successfully!"