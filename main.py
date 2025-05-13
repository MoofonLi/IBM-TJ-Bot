import os
import subprocess
import time
from dotenv import load_dotenv

def run_streamlit_app():
    """執行 Streamlit 應用程序"""
    try:
        # 執行 Streamlit 應用程序
        subprocess.run(
            ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Streamlit 應用程序執行失敗: {e}")
    except KeyboardInterrupt:
        print("使用者中斷程式執行")

def main():
    # 載入環境變數
    load_dotenv()
    
    print("正在啟動 TJBot 控制中心...")
    
    # 檢查所需的環境變數
    required_env_vars = [
        'ASSISTANT_APIKEY', 'ASSISTANT_URL', 'ASSISTANT_ID',
        'TTS_APIKEY', 'TTS_URL',
        'STT_APIKEY', 'STT_URL'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"錯誤: 缺少以下環境變數: {', '.join(missing_vars)}")
        print("請確保 .env 檔案包含所有必要的 API 金鑰和 URL")
        return
    
    try:
        # 執行 Streamlit 應用程序
        run_streamlit_app()
    except Exception as e:
        print(f"程式執行錯誤: {e}")
    finally:
        # 確保在結束時清理資源
        try:
            from utils.hardware_control import HardwareControl
            hardware = HardwareControl()
            hardware.shine("off")  # 關閉 LED
            hardware.lower_arm()   # 放下手臂
            hardware.cleanup()
            print("硬體資源已清理")
        except Exception as e:
            print(f"清理硬體資源時出錯: {e}")

if __name__ == "__main__":
    main()