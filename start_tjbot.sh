#!/bin/bash

# 設定專案目錄
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

# 初始化 pyenv（確保 pyenv 指令存在）
if ! command -v pyenv &> /dev/null; then
    echo "❌ pyenv not found! Please install pyenv first."
    exit 1
fi

# 載入 pyenv 環境（若尚未在 .bashrc 設定）
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# 設定 Python 版本
echo "⚙️ Setting Python 3.11.2 for this project..."
pyenv local 3.11.2

# 顯示使用中的 python
echo "✅ Using Python: $(which python)"

# 檢查虛擬環境是否存在
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# 啟動虛擬環境
echo "🔄 Activating virtual environment..."
source .venv/bin/activate || {
    echo "❌ Failed to activate virtual environment. File not found: .venv/bin/activate"
    exit 1
}

# 確保 pip 可用
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found! Trying to install it..."
    python -m ensurepip --upgrade
fi

# 更新 pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# 檢查是否已安裝 ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Error: ffmpeg is not installed!"
    echo "請先執行 install_dependencies.sh："
    echo "chmod +x install_dependencies.sh && ./install_dependencies.sh"
    exit 1
fi

# 安裝 Python 相依套件
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install --upgrade streamlit audio-recorder-streamlit

# 檢查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "請建立 .env 檔案並填入 API 金鑰等資訊。"
    exit 1
fi

# 載入環境變數
echo "🌱 Loading environment variables..."
source .env

# 設定 ngrok 認證
if [ -n "$NGROK_AUTHTOKEN" ]; then
    echo "🔐 Setting up ngrok authentication..."
    ngrok config add-authtoken "$NGROK_AUTHTOKEN"
else
    echo "❌ Error: NGROK_AUTHTOKEN not found in .env file!"
    exit 1
fi

# 啟動應用
echo "🚀 Starting TJBot Controller..."
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: streamlit not found in the virtual environment!"
    exit 1
fi
streamlit run app.py --server.port 8501 --server.headless true &

# 等待應用啟動
echo "⏳ Waiting for application to start..."
sleep 5

# 啟動 ngrok
echo "🌍 Starting ngrok tunnel..."
ngrok http 8501
