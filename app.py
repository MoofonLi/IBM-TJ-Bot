import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import subprocess
import threading
from utils.watson_assistant import WatsonAssistant
from utils.text_to_speech import TextToSpeech
from utils.hardware_control import HardwareControl
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from audio_recorder_streamlit import audio_recorder

# 載入環境變數
load_dotenv()

# 設定 Streamlit 頁面配置
st.set_page_config(
    page_title="TJBot 控制台",
    page_icon="🤖",
    layout="wide"
)

# 初始化 Session State
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'assistant' not in st.session_state:
    st.session_state.assistant = None
if 'tts' not in st.session_state:
    st.session_state.tts = None
if 'stt' not in st.session_state:
    st.session_state.stt = None
if 'hardware' not in st.session_state:
    st.session_state.hardware = None
if 'system_status' not in st.session_state:
    st.session_state.system_status = "未初始化"
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)

    def recognize_audio(self, audio_data, content_type='audio/webm'):
        """識別音訊檔案"""
        try:
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type=content_type,
                model='en-US_BroadbandModel',
            ).get_result()

            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                return transcript
            else:
                return ""
        except Exception as e:
            st.error(f"語音識別錯誤: {e}")
            return ""

def convert_webm_to_wav(webm_data):
    """將 webm 音頻轉換為 wav 格式"""
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_webm:
        temp_webm.write(webm_data)
        webm_path = temp_webm.name
    
    wav_path = webm_path.replace('.webm', '.wav')
    try:
        subprocess.run(['ffmpeg', '-i', webm_path, '-ac', '1', '-ar', '16000', wav_path], 
                      check=True, capture_output=True)
        
        with open(wav_path, 'rb') as wav_file:
            wav_data = wav_file.read()
        
        # 清理臨時文件
        os.unlink(webm_path)
        os.unlink(wav_path)
        
        return wav_data
    except subprocess.CalledProcessError as e:
        st.error(f"音頻轉換失敗: {e}")
        os.unlink(webm_path)
        return None

def test_system():
    """測試系統所有組件"""
    test_results = {
        "Watson Assistant": False,
        "Text to Speech": False,
        "Speech to Text": False,
        "硬體控制": False
    }
    
    try:
        # 先嘗試清理 GPIO 資源
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            import time
            time.sleep(1)  # 等待 GPIO 重置
        except Exception as e:
            print(f"GPIO 清理失敗: {e}")
        
        # 初始化 Watson Assistant
        st.session_state.assistant = WatsonAssistant(
            os.getenv('ASSISTANT_APIKEY'),
            os.getenv('ASSISTANT_URL'),
            os.getenv('ASSISTANT_ID'),
            version='2023-04-15'
        )
        test_results["Watson Assistant"] = True
        
        # 初始化 Text to Speech
        st.session_state.tts = TextToSpeech(
            os.getenv('TTS_APIKEY'),
            os.getenv('TTS_URL')
        )
        test_results["Text to Speech"] = True
        
        # 初始化 Speech to Text
        st.session_state.stt = SpeechToText(
            os.getenv('STT_APIKEY'),
            os.getenv('STT_URL')
        )
        test_results["Speech to Text"] = True
        
        # 初始化硬體控制
        st.session_state.hardware = HardwareControl()
        test_results["硬體控制"] = True
        
        # 更新系統狀態
        if all(test_results.values()):
            st.session_state.system_status = "系統已就緒"
        else:
            failed_components = [k for k, v in test_results.items() if not v]
            st.session_state.system_status = f"部分組件初始化失敗: {', '.join(failed_components)}"
        
        return test_results
    except Exception as e:
        st.session_state.system_status = f"系統初始化失敗: {str(e)}"
        return test_results

def shutdown_system():
    """關閉系統所有組件"""
    try:
        # 關閉硬體
        if st.session_state.hardware:
            try:
                # 關閉 LED
                st.session_state.hardware.shine("off")
            except Exception as e:
                print(f"關閉 LED 失敗: {e}")
                
            try:
                # 放下手臂
                st.session_state.hardware.lower_arm()
            except Exception as e:
                print(f"放下手臂失敗: {e}")
                
            try:
                # 清理GPIO
                st.session_state.hardware.cleanup()
            except Exception as e:
                print(f"硬體清理失敗: {e}")
            
            try:
                # 額外的 GPIO 清理
                import RPi.GPIO as GPIO
                GPIO.cleanup()
            except Exception as e:
                print(f"GPIO 清理失敗: {e}")
                
            st.session_state.hardware = None
        
        # 清除 session state
        st.session_state.assistant = None
        st.session_state.tts = None
        st.session_state.stt = None
        st.session_state.system_status = "系統已關閉"
        
        return True
    except Exception as e:
        st.session_state.system_status = f"系統關閉失敗: {str(e)}"
        return False

def process_message(user_input):
    """處理使用者訊息並執行相應動作"""
    if not st.session_state.assistant:
        st.error("服務尚未初始化！")
        return
    
    # 發送到 Watson Assistant
    response = st.session_state.assistant.send_message(user_input)
    
    if response:
        # 處理回應
        intents = response.get('output', {}).get('intents', [])
        entities = response.get('output', {}).get('entities', [])
        response_texts = response.get('output', {}).get('generic', [])
        
        # 顯示回應
        bot_reply = ""
        for text in response_texts:
            if text['response_type'] == 'text':
                bot_reply += text['text'] + " "
        
        # 保存對話歷史
        st.session_state.chat_history.append(("使用者", user_input))
        st.session_state.chat_history.append(("TJBot", bot_reply))
        
        # 執行硬體動作
        if intents and st.session_state.hardware:
            top_intent = intents[0]['intent']
            try:
                if top_intent == 'wave':
                    st.session_state.hardware.wave()
                    st.info("機器人揮手 👋")
                elif top_intent == 'lower-arm':
                    st.session_state.hardware.lower_arm()
                    st.info("機器人放下手臂 🙇")
                elif top_intent == 'raise-arm':
                    st.session_state.hardware.raise_arm()
                    st.info("機器人舉起手臂 🙋‍♂️")
                elif top_intent == 'shine':
                    color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                    st.session_state.hardware.shine(color)
                    st.info(f"機器人發光: {color} ✨")
            except Exception as e:
                st.error(f"執行硬體動作失敗: {e}")
        
        # 語音輸出（僅在 TJBot 上）
        if st.session_state.tts and bot_reply:
            with st.spinner("正在合成語音..."):
                try:
                    st.session_state.tts.speak(bot_reply)
                except Exception as e:
                    st.error(f"語音合成失敗: {e}")
        
        return bot_reply
    else:
        st.error("無法獲取 Watson 回應")
        return None

def clear_state():
    """清除狀態回到初始狀態"""
    if st.session_state.hardware:
        try:
            # 關閉 LED
            st.session_state.hardware.shine("off")
        except Exception as e:
            print(f"關閉 LED 失敗: {e}")
            
        try:
            # 放下手臂
            st.session_state.hardware.lower_arm()
        except Exception as e:
            print(f"放下手臂失敗: {e}")
    
    # 清除聊天記錄
    st.session_state.chat_history = []

# 主頁面
def main():
    st.title("🤖 TJBot 控制台")
    
    # 移除自動初始化系統部分
    
    # 側邊欄 - 狀態和控制
    with st.sidebar:
        st.header("系統狀態")
        st.write(f"狀態: {st.session_state.system_status}")
        
        # 系統初始化按鈕
        if st.button("初始化系統"):
            with st.spinner("正在初始化系統..."):
                test_results = test_system()
                
                # 顯示測試結果
                if all(test_results.values()):
                    st.success("系統初始化完成")
                else:
                    st.warning("部分組件初始化失敗")
                
                for component, status in test_results.items():
                    if status:
                        st.write(f"✅ {component}")
                    else:
                        st.write(f"❌ {component}")
        
        # 關閉系統按鈕
        if st.button("關閉系統"):
            with st.spinner("正在關閉系統..."):
                if shutdown_system():
                    st.success("系統已安全關閉")
                else:
                    st.error("系統關閉失敗")
        
        # 手動硬體控制
        st.header("手動控制")
        
        # 語音按鈕
        voice_col1, voice_col2 = st.columns(2)
        with voice_col1:
            st.subheader("語音輸入")
            
            # 初始化錄音區域
            audio_placeholder = st.empty()
            
            # 錄音按鈕
            if st.button("🎤 開始錄音"):
                if st.session_state.stt:
                    with audio_placeholder:
                        audio_bytes = audio_recorder(
                            text="正在錄音...",
                            recording_color="#e8b62c",
                            neutral_color="#6aa36f",
                            icon_name="microphone",
                            icon_size="2x",
                            stopped_text="停止錄音"
                        )
                        
                        if audio_bytes:
                            with st.spinner("正在識別語音..."):
                                # 轉換音頻格式
                                wav_data = convert_webm_to_wav(audio_bytes)
                                
                                if wav_data:
                                    # 進行語音識別
                                    user_input = st.session_state.stt.recognize_audio(wav_data, content_type='audio/wav')
                                    
                                    if user_input:
                                        # 處理訊息
                                        process_message(user_input)
                                        # 避免使用 st.experimental_rerun()，改用其他方式更新 UI
                                        st.success(f"收到語音輸入: {user_input}")
                                    else:
                                        st.error("無法識別語音，請再試一次")
                                else:
                                    st.error("音頻格式轉換失敗")
                else:
                    st.error("語音識別服務未初始化")
        
        st.subheader("動作控制")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👋 揮手"):
                if st.session_state.hardware:
                    try:
                        st.session_state.hardware.wave()
                        st.success("已揮手")
                    except Exception as e:
                        st.error(f"揮手失敗: {e}")
                else:
                    st.error("硬體未初始化")
            
            if st.button("🙋‍♂️ 舉手"):
                if st.session_state.hardware:
                    try:
                        st.session_state.hardware.raise_arm()
                        st.success("已舉手")
                    except Exception as e:
                        st.error(f"舉手失敗: {e}")
                else:
                    st.error("硬體未初始化")
        
        with col2:
            if st.button("🙇 放下手"):
                if st.session_state.hardware:
                    try:
                        st.session_state.hardware.lower_arm()
                        st.success("已放下手")
                    except Exception as e:
                        st.error(f"放下手失敗: {e}")
                else:
                    st.error("硬體未初始化")
            
            color = st.selectbox("LED 顏色", ["red", "green", "blue", "white", "off"])
            if st.button("💡 設定燈光"):
                if st.session_state.hardware:
                    try:
                        st.session_state.hardware.shine(color)
                        st.success(f"已設定燈光為 {color}")
                    except Exception as e:
                        st.error(f"設定燈光失敗: {e}")
                else:
                    st.error("硬體未初始化")
    
    # 主要區域 - 聊天介面
    st.header("對話區域")
    
    # 顯示聊天歷史
    chat_container = st.container()
    with chat_container:
        for role, message in st.session_state.chat_history:
            if role == "使用者":
                st.text_area(f"使用者", value=message, height=50, disabled=True, key=f"user_{len(st.session_state.chat_history)}_{message[:10]}")
            else:
                st.text_area(f"TJBot", value=message, height=100, disabled=True, key=f"bot_{len(st.session_state.chat_history)}_{message[:10]}")
    
    # 文字輸入
    user_input = st.text_input("請輸入訊息...")
    send_button = st.button("發送")
    
    if send_button and user_input:
        with st.spinner("處理中..."):
            process_message(user_input)
            # 避免使用 st.experimental_rerun()
            st.success("訊息已發送")
    
    # 清除狀態按鈕
    if st.button("清除狀態"):
        clear_state()
        st.success("已清除狀態")
    
    # 頁腳
    st.text("TJBot 控制台 - powered by IBM Watson AI")

if __name__ == "__main__":
    main()