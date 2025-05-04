import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import subprocess
import wave
import numpy as np
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
    page_title="TJBot Controller",
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
if 'initialization_status' not in st.session_state:
    st.session_state.initialization_status = "未初始化"

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
        # 使用 ffmpeg 轉換格式（確保已安裝）
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

def initialize_components():
    """初始化所有元件"""
    try:
        # 初始化 Watson Assistant
        st.session_state.assistant = WatsonAssistant(
            os.getenv('ASSISTANT_APIKEY'),
            os.getenv('ASSISTANT_URL'),
            os.getenv('ASSISTANT_ID'),
            version='2023-04-15'
        )
        
        # 初始化 Text to Speech
        st.session_state.tts = TextToSpeech(
            os.getenv('TTS_APIKEY'),
            os.getenv('TTS_URL')
        )
        
        # 初始化 Speech to Text
        st.session_state.stt = SpeechToText(
            os.getenv('STT_APIKEY'),
            os.getenv('STT_URL')
        )
        
        # 初始化硬體控制
        st.session_state.hardware = HardwareControl()
        
        st.session_state.initialization_status = "已初始化"
        return True
    except Exception as e:
        st.session_state.initialization_status = f"初始化失敗: {str(e)}"
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
        
        # 語音輸出（使用現有的 text_to_speech）
        if st.session_state.tts and bot_reply:
            with st.spinner("正在合成語音..."):
                # 使用你現有的 text_to_speech.py 中的 speak 方法
                st.session_state.tts.speak(bot_reply)
                
                # 由於 speak 方法會建立 response.wav，我們可以提供給前端播放
                if os.path.exists('response.wav'):
                    st.audio('response.wav', format='audio/wav')
        
        return bot_reply
    else:
        st.error("無法獲取 Watson 回應")
        return None

# 主要介面
st.title("🤖 TJBot Controller")
st.write("透過文字或語音與 TJBot 互動")

# 側邊欄 - 狀態和控制
with st.sidebar:
    st.header("系統狀態")
    
    # 初始化按鈕
    if st.button("初始化系統"):
        with st.spinner("正在初始化..."):
            if initialize_components():
                st.success("系統初始化成功！")
            else:
                st.error("系統初始化失敗！")
    
    st.write(f"狀態: {st.session_state.initialization_status}")
    
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
        
        color = st.selectbox("LED 顏色", ["red", "green", "blue", "white"])
        if st.button("💡 點亮"):
            if st.session_state.hardware:
                st.session_state.hardware.shine(color)
            else:
                st.error("硬體未初始化")

# 主要區域 - 聊天介面
st.header("對話區域")

# 顯示聊天歷史
for role, message in st.session_state.chat_history:
    if role == "使用者":
        st.chat_message("user").write(message)
    else:
        st.chat_message("assistant").write(message)

# 輸入方式選擇
input_mode = st.radio("選擇輸入方式", ["文字", "語音"])

if input_mode == "文字":
    # 文字輸入
    user_input = st.chat_input("請輸入訊息...")
    
    if user_input:
        st.chat_message("user").write(user_input)
        with st.spinner("處理中..."):
            process_message(user_input)
else:
    # 語音輸入
    st.write("點擊下方按鈕開始錄音：")
    
    audio_bytes = audio_recorder(
        text="點擊錄音",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="4x",
    )
    
    if audio_bytes and st.session_state.stt:
        with st.spinner("正在識別語音..."):
            # 轉換音頻格式
            wav_data = convert_webm_to_wav(audio_bytes)
            
            if wav_data:
                # 進行語音識別
                user_input = st.session_state.stt.recognize_audio(wav_data, content_type='audio/wav')
                
                if user_input:
                    st.chat_message("user").write(user_input)
                    with st.spinner("處理中..."):
                        process_message(user_input)
                else:
                    st.error("無法識別語音，請再試一次")
            else:
                st.error("音頻格式轉換失敗")

# 頁腳
st.markdown("---")
st.markdown("TJBot Controller - powered by IBM Watson AI")