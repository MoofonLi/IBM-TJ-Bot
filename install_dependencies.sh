#!/bin/bash

set -e

echo "🔧 正在更新套件列表..."
sudo apt update

echo "📦 安裝基本開發工具與 pyenv 所需依賴..."
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev git

echo "✅ 系統依賴安裝完成。"

# 安裝 pyenv（如尚未安裝）
if ! command -v pyenv &> /dev/null; then
    echo "🌱 安裝 pyenv..."
    curl https://pyenv.run | bash

    echo "🔁 設定 pyenv 環境變數..."
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
else
    echo "✅ pyenv 已安裝。"
fi
