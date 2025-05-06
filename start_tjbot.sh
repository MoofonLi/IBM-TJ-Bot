#!/bin/bash

# 設定專案目錄
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

# 設置 Python 3.11.2 為當前目錄的預設版本
echo "Setting Python 3.11.2 for this project..."
pyenv local 3.11.2

# 檢查虛擬環境是否存在
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# 啟動虛擬環境
echo "Activating virtual environment..."
source .venv/bin/activate

# 確保 pip 是最新的
echo "Upgrading pip..."
pip install --upgrade pip

# 檢查系統依賴是否安裝
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed!"
    echo "Please run install_dependencies.sh first:"
    echo "chmod +x install_dependencies.sh && ./install_dependencies.sh"
    exit 1
fi

# 檢查並安裝 Python 套件
echo "Checking and installing Python dependencies..."
pip install -r requirements.txt

# 檢查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with your API credentials"
    exit 1
fi

# 載入 .env 檔案中的變數
echo "Loading environment variables..."
source .env

# 設置 ngrok 認證
if [ -n "$NGROK_AUTHTOKEN" ]; then
    echo "Setting up ngrok authentication..."
    ngrok config add-authtoken "$NGROK_AUTHTOKEN"
else
    echo "Error: NGROK_AUTHTOKEN not found in .env file!"
    exit 1
fi

# 啟動 Streamlit 應用
echo "Starting TJBot Controller..."
streamlit run app.py --server.port 8501 --server.headless true &

# 等待應用啟動
echo "Waiting for application to start..."
sleep 5

# 啟動 ngrok 隧道
echo "Starting ngrok tunnel..."
ngrok http 8501