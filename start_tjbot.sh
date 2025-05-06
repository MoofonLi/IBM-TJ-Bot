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

# 修改 requirements.txt 中 audio-recorder-streamlit 的版本（如果需要）
if grep -q "audio-recorder-streamlit==0.1.10" requirements.txt; then
    echo "Updating audio-recorder-streamlit version in requirements.txt..."
    sed -i 's/audio-recorder-streamlit==0.1.10/audio-recorder-streamlit==0.0.10/g' requirements.txt
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

# 直接設置環境變數而不是通過 source
echo "Loading environment variables..."
export ASSISTANT_APIKEY=$(grep ASSISTANT_APIKEY .env | cut -d "'" -f 2)
export ASSISTANT_URL=$(grep ASSISTANT_URL .env | cut -d "'" -f 2)
export ASSISTANT_ID=$(grep ASSISTANT_ID .env | cut -d "'" -f 2)
export TTS_APIKEY=$(grep TTS_APIKEY .env | cut -d "'" -f 2)
export TTS_URL=$(grep TTS_URL .env | cut -d "'" -f 2)
export STT_APIKEY=$(grep STT_APIKEY .env | cut -d "'" -f 2)
export STT_URL=$(grep STT_URL .env | cut -d "'" -f 2)
export NGROK_AUTHTOKEN=$(grep NGROK_AUTHTOKEN .env | cut -d "'" -f 2)

# 設置 ngrok 認證 (使用 sudo -E 保留環境變數)
if [ -n "$NGROK_AUTHTOKEN" ]; then
    echo "Setting up ngrok authentication..."
    sudo -E ngrok config add-authtoken "$NGROK_AUTHTOKEN"
else
    echo "Error: NGROK_AUTHTOKEN not found in .env file!"
    exit 1
fi

# 確定 streamlit 的完整路徑（在當前虛擬環境中）
STREAMLIT_PATH="$PROJECT_DIR/.venv/bin/streamlit"
echo "Streamlit path: $STREAMLIT_PATH"

# 檢查 app.py 是否存在，如果不存在則創建一個簡單的版本
if [ ! -f "app.py" ]; then
    echo "Creating a simple app.py for testing..."
    cat > app.py << 'EOF'
import streamlit as st
import os

st.title("TJ Bot 測試頁面")
st.write("如果您看到這個頁面，表示 Streamlit 已成功運行！")
st.write("環境變數測試:")
st.write(f"ASSISTANT_ID: {os.getenv('ASSISTANT_ID', '未設置')}")
EOF
fi

# 使用完整路徑啟動 Streamlit 應用
echo "Starting TJBot Controller with admin privileges..."
if [ -x "$STREAMLIT_PATH" ]; then
    echo "Using Streamlit from virtual environment: $STREAMLIT_PATH"
    sudo -E "$STREAMLIT_PATH" run app.py --server.port 8501 --server.headless true &
else
    echo "WARNING: Streamlit not found in virtual environment, trying with module import..."
    sudo -E python -m streamlit run app.py --server.port 8501 --server.headless true &
fi

# 等待應用啟動
echo "Waiting for application to start..."
sleep 5

# 使用 sudo -E 啟動 ngrok 隧道
echo "Starting ngrok tunnel with admin privileges..."
sudo -E ngrok http 8501