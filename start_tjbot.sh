#!/bin/bash

# 設定專案目錄
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

# 檢查虛擬環境是否存在
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv .venv
fi

# 啟動虛擬環境
echo "Activating virtual environment..."
source .venv/bin/activate

# 檢查並安裝必要套件
echo "Checking and installing dependencies..."
pip install -r requirements.txt
pip install --upgrade streamlit audio-recorder-streamlit

# 檢查 ffmpeg 是否安裝（用於音頻轉換）
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Please install it first:"
    echo "sudo apt update && sudo apt install ffmpeg"
    exit 1
fi

# 檢查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with your API credentials"
    exit 1
fi

# 啟動 Streamlit 應用
echo "Starting TJBot Controller..."
streamlit run app.py --server.port 8501 --server.headless true &

# 等待應用啟動
echo "Waiting for application to start..."
sleep 10

# 啟動 ngrok 隧道（可選）
if command -v ngrok &> /dev/null && [ -n "$NGROK_AUTHTOKEN" ]; then
    echo "Starting ngrok tunnel..."
    ngrok http 8501
else
    echo "ngrok not installed or NGROK_AUTHTOKEN not set"
    echo "Application is available at http://localhost:8501"
fi