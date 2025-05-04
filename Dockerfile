FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libsndfile1 \
    alsa-utils \
    ffmpeg \
    pulseaudio \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝專案依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 暴露容器埠
EXPOSE 8501

# 啟動應用
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]