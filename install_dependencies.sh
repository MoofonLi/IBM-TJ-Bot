#!/bin/bash

# 安裝系統依賴
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev python-openssl git ffmpeg portaudio19-dev python3-pyaudio

# 安裝 pyenv（如果尚未安裝）
if [ ! -d "$HOME/.pyenv" ]; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash

    echo "Configuring pyenv environment..."
    echo -e '\n# pyenv setup' >> ~/.bashrc
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

    echo "Please restart your terminal or run: source ~/.bashrc"
else
    echo "pyenv already installed."
fi

echo "System dependencies installed successfully!"
