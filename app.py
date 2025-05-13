import streamlit as st
import os
from dotenv import load_dotenv
from utils.watson_assistant import WatsonAssistant
from utils.text_to_speech import TextToSpeech
from utils.hardware_control import HardwareControl
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# 載入環境變數
load_dotenv()

# 設定頁面
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
if 'hardware' not in st.session_state:
    st.session_state.hardware = None
if 'system_status' not in st.session_state:
    st.session_state.system_status = "未初始化"

def initialize_system():
    """初始化系統組件"""
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
        
        # 初始化硬體控制
        st.session_state.hardware = HardwareControl()
        
        st.session_state.system_status = "系統已就緒"
        return True
    except Exception as e:
        st.session_state.system_status = f"初始化失敗: {str(e)}"
        return False

def shutdown_system():
    """關閉系統組件"""
    try:
        if st.session_state.hardware:
            st.session_state.hardware.shine("off")
            st.session_state.hardware.lower_arm()
            st.session_state.hardware.cleanup()
        
        st.session_state.assistant = None
        st.session_state.tts = None
        st.session_state.hardware = None
        st.session_state.system_status = "系統已關閉"
        return True
    except Exception as e:
        return False

def process_message(user_input):
    """處理使用者訊息"""
    if not st.session_state.assistant:
        st.error("系統未初始化!")
        return None
    
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
        
        # 保存對話
        st.session_state.chat_history.append(("使用者", user_input))
        st.session_state.chat_history.append(("TJBot", bot_reply))
        
        # 執行硬體動作
        if intents and st.session_state.hardware:
            top_intent = intents[0]['intent']
            if top_intent == 'wave':
                st.session_state.hardware.wave()
            elif top_intent == 'lower-arm':
                st.session_state.hardware.lower_arm()
            elif top_intent == 'raise-arm':
                st.session_state.hardware.raise_arm()
            elif top_intent == 'shine':
                color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                st.session_state.hardware.shine(color)
        
        # 語音輸出
        if st.session_state.tts and bot_reply:
            st.session_state.tts.speak(bot_reply)
        
        return bot_reply
    else:
        return None

def clear_state():
    """清除狀態"""
    if st.session_state.hardware:
        st.session_state.hardware.shine("off")
        st.session_state.hardware.lower_arm()
    st.session_state.chat_history = []

# 主頁面
st.title("🤖 TJBot 控制台")

# 自動初始化
if st.session_state.system_status == "未初始化":
    with st.spinner("正在初始化系統..."):
        if initialize_system():
            st.success("系統初始化完成")
        else:
            st.error("系統初始化失敗")

# 側邊欄
with st.sidebar:
    st.header("系統狀態")
    st.write(f"狀態: {st.session_state.system_status}")
    
    # 系統控制
    if st.button("系統測試"):
        with st.spinner("測試中..."):
            if initialize_system():
                st.success("測試通過")
            else:
                st.error("測試失敗")
    
    if st.button("關閉系統"):
        with st.spinner("關閉中..."):
            if shutdown_system():
                st.success("系統已關閉")
            else:
                st.error("關閉失敗")
    
    # 硬體控制
    st.header("硬體控制")
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
        
        color = st.selectbox("燈光顏色", ["red", "green", "blue", "white", "off"])
        if st.button("💡 設定燈光"):
            if st.session_state.hardware:
                st.session_state.hardware.shine(color)
            else:
                st.error("硬體未初始化")

# 主要聊天區域
st.header("對話區域")

# 顯示聊天歷史
for role, message in st.session_state.chat_history:
    if role == "使用者":
        st.text_area("使用者", message, height=50, disabled=True)
    else:
        st.text_area("TJBot", message, height=100, disabled=True)

# 文字輸入
user_input = st.text_input("輸入訊息")
send_button = st.button("發送")

if send_button and user_input:
    with st.spinner("處理中..."):
        process_message(user_input)
    st.empty()  # 清空輸入框

# 清除狀態按鈕
if st.button("清除狀態"):
    clear_state()
    st.success("已清除狀態")

# 頁腳
st.text("TJBot 控制台 - powered by IBM Watson AI")