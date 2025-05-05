#!/bin/bash

# 設定專案目錄
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

# 創建新的虛擬環境（如果不存在）
if ! pyenv versions | grep -q "3.11.2/envs/tjbot-venv"; then
    echo "Creating virtual environment..."
    pyenv virtualenv 3.11.2 tjbot-venv
fi

# 設置專案使用此虛擬環境
echo "Setting local Python environment..."
pyenv local tjbot-venv

# 確保 pip 是最新的
echo "Upgrading pip..."
pip install --upgrade pip

# 安裝 Python 套件
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install --upgrade streamlit audio-recorder-streamlit

# 檢查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# 載入環境變數
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