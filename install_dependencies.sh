#!/bin/bash

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev \
xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 python3-dev ffmpeg

# 安裝 pyenv（如果尚未安裝）
if [ ! -d "$HOME/.pyenv" ]; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash

    echo "Configuring pyenv environment..."
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
    source ~/.bashrc
else
    echo "pyenv already installed."
fi

# 載入 pyenv
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# 安裝 Python 3.11.2（如果尚未安裝）
if ! pyenv versions | grep -q "3.11.2"; then
    echo "Installing Python 3.11.2 with pyenv..."
    pyenv install -v 3.11.2
else
    echo "Python 3.11.2 already installed via pyenv."
fi

echo "System dependencies and Python 3.11.2 installed successfully!"
