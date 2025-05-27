#!/bin/bash

set -e

# 確保 pyenv 在 PATH 裡
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

echo "🐍 安裝 Python 3.11.2（如尚未安裝）..."
if ! pyenv versions | grep -q "3.11.2"; then
    pyenv install 3.11.2
fi

echo "📌 設定專案使用 Python 3.11.2..."
pyenv local 3.11.2

echo "🧪 建立虛擬環境 .venv..."
python -m venv .venv

echo "⚙️ 啟動虛擬環境..."
source .venv/bin/activate

echo "📦 安裝 Python 套件依賴..."
if [ -f requirements.txt ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️ 找不到 requirements.txt，請確認是否存在。"
fi

echo "🚀 啟動 TJBot 主程式..."
if [ -f run.py ]; then
    sudo .venv/bin/python run.py
else
    echo "❌ 找不到 run.py，請確認程式是否存在於當前目錄。"
fi
