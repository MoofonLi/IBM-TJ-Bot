#!/bin/bash

# ====== 路徑設定 ======
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

# ====== pyenv 初始化（如果有）======
if command -v pyenv >/dev/null 2>&1; then
    echo "Initializing pyenv..."
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

    # 確保使用 3.11.2
    if ! pyenv versions | grep -q "3.11.2"; then
        echo "Installing Python 3.11.2..."
        pyenv install 3.11.2
    fi

    echo "Setting Python 3.11.2 locally..."
    pyenv local 3.11.2
else
    echo "⚠️ pyenv not found. Please install pyenv first!"
    exit 1
fi

# ====== 建立虛擬環境 ======
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# ====== 啟動虛擬環境 ======
echo "Activating virtual environment..."
source .venv/bin/activate

# ====== pip 套件管理 ======
echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
export BLINKA_FORCECHIP=BCM2XXX
pip install -r requirements.txt

# ====== 檢查 .env 檔案 ======
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it first!"
    exit 1
fi

# ====== 載入環境變數 ======
echo "Loading environment variables..."
source .env

# ====== 確保提前輸入密碼 ======
echo "Requesting sudo password..."
sudo true

# ====== 啟動 Streamlit 應用 ======
echo "Starting TJBot Controller..."
sudo -E $(which streamlit) run app.py --server.port 8501 --server.headless true