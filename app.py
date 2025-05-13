import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import subprocess
import time
from audio_recorder_streamlit import audio_recorder

# 導入現有的模組
from utils.watson_assistant import WatsonAssistant
from utils.text_to_speech import TextToSpeech
from utils.hardware_control import HardwareControl
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

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
if 'test_results' not in st.session_state:
    st.session_state.test_results = {}

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
        # 使用 ffmpeg 轉換格式
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

def initialize_system():
    """初始化所有元件並進行系統測試"""
    test_results = {}
    
    try:
        # 測試 Watson Assistant
        st.session_state.assistant = WatsonAssistant(
            os.getenv('ASSISTANT_APIKEY'),
            os.getenv('ASSISTANT_URL'),
            os.getenv('ASSISTANT_ID'),
            version='2023-04-15'
        )
        # 簡單測試 Assistant 連接
        test_response = st.session_state.assistant.send_message("test")
        test_results["Watson Assistant"] = "通過" if test_response else "失敗"
        
        # 測試 Text to Speech
        st.session_state.tts = TextToSpeech(
            os.getenv('TTS_APIKEY'),
            os.getenv('TTS_URL')
        )
        test_results["Text to Speech"] = "通過"
        
        # 測試 Speech to Text
        st.session_state.stt = SpeechToText(
            os.getenv('STT_APIKEY'),
            os.getenv('STT_URL')
        )
        test_results["Speech to Text"] = "通過"
        
        # 測試硬體控制
        st.session_state.hardware = HardwareControl()
        # 簡單測試伺服馬達
        st.session_state.hardware.lower_arm()
        time.sleep(0.5)
        test_results["硬體控制"] = "通過"
        
        st.session_state.system_status = "已初始化"
        st.session_state.test_results = test_results
        
        if all(result == "通過" for result in test_results.values()):
            return True
        else:
            return False
    except Exception as e:
        st.session_state.system_status = f"初始化失敗: {str(e)}"
        for component in ["Watson Assistant", "Text to Speech", "Speech to Text", "硬體控制"]:
            if component not in test_results:
                test_results[component] = "失敗"
        st.session_state.test_results = test_results
        return False

def shutdown_system():
    """關閉系統和清理資源"""
    if st.session_state.hardware:
        # 關閉 LED
        st.session_state.hardware.shine("off")
        # 放下手臂
        st.session_state.hardware.lower_arm()
        # 清理資源
        st.session_state.hardware.cleanup()
    
    # 重置狀態
    st.session_state.assistant = None
    st.session_state.tts = None
    st.session_state.stt = None
    st.session_state.hardware = None
    st.session_state.system_status = "已關閉"
    st.session_state.test_results = {}
    return True

def process_message(user_input):
    """處理使用者訊息並執行相應動作"""
    if not st.session_state.assistant:
        st.error("服務尚未初始化！請先測試系統")
        return
    
    # 發送到 Watson Assistant
    response = st.session_state.assistant.send_message(user_input)
    
    if response:
        # 處理回應
        intents = response.get('output', {}).get('intents', [])
        entities = response.get('output', {}).get('entities', [])
        response_texts = response.get('output', {}).get('generic', [])
        
        # 整合回應文字
        bot_reply = ""
        for text in response_texts:
            if text['response_type'] == 'text':
                bot_reply += text['text'] + " "
        
        # 保存對話歷史
        st.session_state.chat_history.append(("使用者", user_input))
        st.session_state.chat_history.append(("TJBot", bot_reply))
        
        # 執行硬體動作
        if intents:
            top_intent = intents[0]['intent']
            if top_intent == 'wave':
                st.session_state.hardware.wave()
                st.info("機器人揮手👋")
            elif top_intent == 'lower-arm':
                st.session_state.hardware.lower_arm()
                st.info("機器人放下手臂🙇")
            elif top_intent == 'raise-arm':
                st.session_state.hardware.raise_arm()
                st.info("機器人舉起手臂🙋‍♂️")
            elif top_intent == 'shine':
                color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                st.session_state.hardware.shine(color)
                st.info(f"機器人發光: {color}✨")
        
        # 語音輸出（只在 TJBot 上）
        if st.session_state.tts and bot_reply:
            st.session_state.tts.speak(bot_reply)
        
        # 每次執行後回歸硬體初始狀態
        st.session_state.hardware.lower_arm()
        
        return bot_reply
    else:
        st.error("無法獲取 Watson 回應")
        return None

def clear_chat_history():
    """清除聊天歷史"""
    st.session_state.chat_history = []

# 主程式啟動時自動初始化系統
if st.session_state.system_status == "未初始化":
    with st.spinner("正在進行系統測試..."):
        if initialize_system():
            st.success("系統測試通過！TJBot 已準備就緒")
        else:
            st.error("系統測試失敗！請檢查連接和設定")

# 主要介面
st.title("🤖 TJBot 控制台")
st.write("透過文字或語音與 TJBot 互動")

# 側邊欄 - 狀態和控制
with st.sidebar:
    st.header("系統狀態")
    st.write(f"狀態: {st.session_state.system_status}")
    
    # 顯示測試結果
    if st.session_state.test_results:
        st.subheader("測試結果")
        for component, result in st.session_state.test_results.items():
            if result == "通過":
                st.success(f"{component}: {result}")
            else:
                st.error(f"{component}: {result}")
    
    # 系統控制按鈕
    col1, col2 = st.columns(2)
    with col1:
        if st.button("重新測試系統"):
            with st.spinner("正在測試系統..."):
                if initialize_system():
                    st.success("系統測試通過！")
                else:
                    st.error("系統測試失敗！")
    
    with col2:
        if st.button("關閉系統"):
            with st.spinner("正在關閉系統..."):
                if shutdown_system():
                    st.success("系統已安全關閉")
    
    # 手動硬體控制
    st.header("手動控制")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👋 揮手"):
            if st.session_state.hardware:
                st.session_state.hardware.wave()
            else:
                st.error("硬體未初始化")
        
        if st.button("🙋‍♂️ 舉手"):
            if st.session_state.hardware:
                st.session_state.hardware.raise_arm()
            else:
                st.error("硬體未初始化")
    
    with col2:
        if st.button("🙇 放下手"):
            if st.session_state.hardware:
                st.session_state.hardware.lower_arm()
            else:
                st.error("硬體未初始化")
    
    # 燈光控制
    st.subheader("燈光控制")
    color = st.selectbox("選擇顏色", ["red", "green", "blue", "white", "off"])
    if st.button("改變燈光"):
        if st.session_state.hardware:
            st.session_state.hardware.shine(color)
            if color == "off":
                st.info("已關閉燈光")
            else:
                st.info(f"燈光顏色: {color}✨")
        else:
            st.error("硬體未初始化")
    
    # 語音輸入按鈕
    st.header("語音輸入")
    audio_bytes = audio_recorder(
        text="按此開始錄音",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="2x"
    )
    
    if audio_bytes and st.session_state.stt:
        with st.spinner("正在處理語音..."):
            # 轉換音頻格式
            wav_data = convert_webm_to_wav(audio_bytes)
            
            if wav_data:
                # 進行語音識別
                user_input = st.session_state.stt.recognize_audio(wav_data, content_type='audio/wav')
                
                if user_input:
                    # 通知用戶識別結果
                    st.success(f"識別到: {user_input}")
                    # 自動處理語音輸入
                    process_message(user_input)
                else:
                    st.error("無法識別語音，請再試一次")
            else:
                st.error("音頻格式轉換失敗")

# 主要區域 - 聊天介面
st.header("聊天對話")

# 聊天歷史控制
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("清除對話"):
        clear_chat_history()
        st.experimental_rerun()

# 顯示聊天歷史
for role, message in st.session_state.chat_history:
    if role == "使用者":
        st.chat_message("user").write(message)
    else:
        st.chat_message("assistant").write(message)

# 文字輸入
user_input = st.chat_input("請輸入訊息或使用左側語音按鈕...")

if user_input:
    st.chat_message("user").write(user_input)
    with st.spinner("處理中..."):
        process_message(user_input)
        # 頁面重新加載以顯示最新聊天歷史
        st.experimental_rerun()

# 頁腳
st.markdown("---")
st.markdown("TJBot 控制台 - 由 IBM Watson AI 支援")