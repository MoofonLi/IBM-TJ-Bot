import streamlit as st
import os
import tempfile
import subprocess
import threading
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定 Streamlit 頁面配置
st.set_page_config(
    page_title="TJBot 控制中心",
    page_icon="🤖",
    layout="wide"
)

# 初始化 Session State
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False
if 'system_status' not in st.session_state:
    st.session_state.system_status = "未初始化"
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None

# 函數：測試系統組件
def test_system_components():
    """測試各個系統組件是否正常運作"""
    try:
        # 測試 Watson Assistant
        st.write("1. 測試 Watson Assistant 連接...")
        from utils.watson_assistant import WatsonAssistant
        assistant = WatsonAssistant(
            os.getenv('ASSISTANT_APIKEY'),
            os.getenv('ASSISTANT_URL'),
            os.getenv('ASSISTANT_ID'),
            version='2023-04-15'
        )
        test_response = assistant.send_message("Hello")
        if not test_response:
            return False, "Watson Assistant 連接失敗"
        st.write("✅ Watson Assistant 連接成功")
        
        # 測試 Text to Speech
        st.write("2. 測試 Text to Speech 連接...")
        from utils.text_to_speech import TextToSpeech
        tts = TextToSpeech(
            os.getenv('TTS_APIKEY'),
            os.getenv('TTS_URL')
        )
        # 測試生成語音檔但不播放
        tts.speak("測試", play_audio=False)
        if not os.path.exists('response.wav'):
            return False, "Text to Speech 服務失敗"
        st.write("✅ Text to Speech 連接成功")
        
        # 測試硬體控制
        st.write("3. 測試硬體控制...")
        from utils.hardware_control import HardwareControl
        hardware = HardwareControl()
        # 只測試 LED 避免馬達噪音
        hardware.shine("blue")
        time.sleep(1)
        hardware.shine("off")  # 關閉 LED
        hardware.cleanup()
        st.write("✅ 硬體控制測試成功")
        
        return True, "所有系統組件測試成功"
    except Exception as e:
        return False, f"系統測試失敗: {str(e)}"

# 函數：獲取麥克風輸入
def start_recording():
    """開始錄音"""
    st.session_state.is_listening = True
    st.session_state.audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    
    try:
        # 使用 arecord 錄製音頻
        process = subprocess.Popen([
            'arecord', '-D', 'plughw:1,0', '-f', 'cd', 
            '-c', '1', '-r', '44100', '-d', '5',  # 錄製5秒
            st.session_state.audio_file.name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        process.wait()
        st.session_state.is_listening = False
        
        # 檢查錄音是否成功
        if os.path.exists(st.session_state.audio_file.name) and os.path.getsize(st.session_state.audio_file.name) > 0:
            return True
        else:
            return False
    except Exception as e:
        st.error(f"錄音失敗: {e}")
        st.session_state.is_listening = False
        return False

# 函數：處理語音輸入
def process_voice_input():
    """處理語音輸入並轉換為文字"""
    if not st.session_state.audio_file or not os.path.exists(st.session_state.audio_file.name):
        return None
    
    try:
        from ibm_watson import SpeechToTextV1
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        
        # 初始化 Speech to Text
        authenticator = IAMAuthenticator(os.getenv('STT_APIKEY'))
        speech_to_text = SpeechToTextV1(authenticator=authenticator)
        speech_to_text.set_service_url(os.getenv('STT_URL'))
        
        # 讀取音頻檔案
        with open(st.session_state.audio_file.name, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # 識別語音
        result = speech_to_text.recognize(
            audio=audio_data,
            content_type='audio/wav',
            model='en-US_BroadbandModel',
        ).get_result()
        
        # 刪除臨時音頻檔案
        os.unlink(st.session_state.audio_file.name)
        st.session_state.audio_file = None
        
        # 提取轉錄文本
        if 'results' in result and len(result['results']) > 0:
            transcript = result['results'][0]['alternatives'][0]['transcript']
            return transcript.strip()
        else:
            return None
    except Exception as e:
        st.error(f"語音識別錯誤: {e}")
        if st.session_state.audio_file and os.path.exists(st.session_state.audio_file.name):
            os.unlink(st.session_state.audio_file.name)
            st.session_state.audio_file = None
        return None

# 函數：發送訊息到 Watson Assistant 並處理回應
def process_message(user_input):
    """處理使用者訊息並執行相應動作"""
    if not user_input:
        return
    
    # 更新聊天歷史
    st.session_state.chat_history.append(("使用者", user_input))
    
    try:
        from utils.watson_assistant import WatsonAssistant
        from utils.text_to_speech import TextToSpeech
        from utils.hardware_control import HardwareControl
        
        # 初始化服務
        assistant = WatsonAssistant(
            os.getenv('ASSISTANT_APIKEY'),
            os.getenv('ASSISTANT_URL'),
            os.getenv('ASSISTANT_ID'),
            version='2023-04-15'
        )
        tts = TextToSpeech(
            os.getenv('TTS_APIKEY'),
            os.getenv('TTS_URL')
        )
        hardware = HardwareControl()
        
        # 發送訊息到 Watson Assistant
        response = assistant.send_message(user_input)
        
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
            st.session_state.chat_history.append(("TJBot", bot_reply))
            
            # 執行硬體動作（依據 Watson Assistant 辨識的意圖）
            if intents:
                top_intent = intents[0]['intent']
                if top_intent == 'wave':
                    hardware.wave()
                    st.sidebar.success("機器人揮手👋")
                elif top_intent == 'lower-arm':
                    hardware.lower_arm()
                    st.sidebar.success("機器人放下手臂🙇")
                elif top_intent == 'raise-arm':
                    hardware.raise_arm()
                    st.sidebar.success("機器人舉起手臂🙋‍♂️")
                elif top_intent == 'shine':
                    # 從 entities 提取顏色
                    color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                    hardware.shine(color)
                    st.sidebar.success(f"機器人發光: {color}✨")
            
            # 語音輸出（僅在 TJBot 上）
            if bot_reply:
                tts.speak(bot_reply)
            
            # 清理硬體資源
            hardware.cleanup()
            
            return bot_reply
    except Exception as e:
        st.error(f"處理訊息時出錯: {str(e)}")
        st.session_state.chat_history.append(("系統", f"錯誤: {str(e)}"))
        return None

# 函數：執行 Watson Assistant 指令
def execute_assistant_command(command):
    """傳送特定指令到 Watson Assistant 並執行回應的動作"""
    # 直接呼叫 process_message 函數處理命令
    process_message(command)

# 函數：關閉系統
def shutdown_system():
    """關閉系統並清理資源"""
    try:
        from utils.hardware_control import HardwareControl
        hardware = HardwareControl()
        hardware.shine("off")  # 關閉 LED
        hardware.lower_arm()  # 放下手臂
        hardware.cleanup()
        st.session_state.system_initialized = False
        st.session_state.system_status = "已關閉"
        return True
    except Exception as e:
        st.error(f"關閉系統時出錯: {str(e)}")
        return False

# 主要介面
st.title("🤖 TJBot 控制中心")

# 側邊欄 - 狀態和控制
with st.sidebar:
    st.header("系統狀態")
    
    # 系統初始化
    if not st.session_state.system_initialized:
        with st.spinner("正在測試系統組件..."):
            success, message = test_system_components()
            if success:
                st.session_state.system_initialized = True
                st.session_state.system_status = "已初始化"
                st.success(message)
            else:
                st.error(message)
    
    st.write(f"狀態: {st.session_state.system_status}")
    
    # 重新測試按鈕
    if st.button("重新測試系統"):
        with st.spinner("正在測試系統組件..."):
            success, message = test_system_components()
            if success:
                st.session_state.system_initialized = True
                st.session_state.system_status = "已初始化"
                st.success(message)
            else:
                st.session_state.system_initialized = False
                st.session_state.system_status = "測試失敗"
                st.error(message)
    
    # 關閉系統按鈕
    if st.session_state.system_initialized and st.button("關閉系統"):
        with st.spinner("正在關閉系統..."):
            if shutdown_system():
                st.success("系統已關閉")
            else:
                st.error("關閉系統失敗")
    
    # 手動指令控制（透過 Watson Assistant）
    st.header("指令控制")
    
    # 揮手指令
    if st.button("👋 揮手"):
        if st.session_state.system_initialized:
            execute_assistant_command("請揮手")
        else:
            st.error("系統未初始化")
    
    # 舉手指令
    if st.button("🙋‍♂️ 舉手"):
        if st.session_state.system_initialized:
            execute_assistant_command("請舉起手")
        else:
            st.error("系統未初始化")
    
    # 放下手指令
    if st.button("🙇 放下手"):
        if st.session_state.system_initialized:
            execute_assistant_command("請放下手")
        else:
            st.error("系統未初始化")
    
    # 顏色控制
    st.subheader("LED 控制")
    color = st.selectbox("選擇顏色", ["red", "green", "blue", "white"])
    
    # 點亮 LED 指令
    if st.button("💡 點亮 LED"):
        if st.session_state.system_initialized:
            execute_assistant_command(f"請將燈變成{color}色")
        else:
            st.error("系統未初始化")
    
    # 關燈指令
    if st.button("🔅 關燈"):
        if st.session_state.system_initialized:
            execute_assistant_command("請關燈")
        else:
            st.error("系統未初始化")
    
    # 語音輸入按鈕
    st.header("語音輸入")
    
    if st.session_state.is_listening:
        st.write("🎙️ 正在聆聽...")
        st.warning("請說出您的指令...")
    else:
        if st.button("🎙️ 開始錄音 (5秒)"):
            if st.session_state.system_initialized:
                # 開始新線程進行錄音
                recording_thread = threading.Thread(target=start_recording)
                recording_thread.start()
                
                # 等待錄音完成
                with st.spinner("正在錄音..."):
                    recording_thread.join()
                
                # 處理錄音結果
                with st.spinner("正在識別語音..."):
                    user_input = process_voice_input()
                    
                    if user_input:
                        st.success(f"識別到: {user_input}")
                        # 處理識別到的語音輸入
                        process_message(user_input)
                        # 強制重新載入頁面以更新聊天歷史
                        st.experimental_rerun()
                    else:
                        st.error("無法識別語音，請重試")
            else:
                st.error("系統未初始化")

# 主要區域 - 聊天介面
st.header("對話區域")

# 顯示聊天歷史
chat_container = st.container()
with chat_container:
    for role, message in st.session_state.chat_history:
        if role == "使用者":
            st.chat_message("user").write(message)
        elif role == "TJBot":
            st.chat_message("assistant").write(message)
        else:
            st.warning(message)

# 文字輸入
user_input = st.chat_input("請輸入訊息...")

if user_input:
    # 處理使用者輸入
    with st.spinner("處理中..."):
        process_message(user_input)
        # 強制重新載入頁面以更新聊天歷史
        st.experimental_rerun()

# 頁腳
st.markdown("---")
st.markdown("TJBot 控制中心 - 由 IBM Watson AI 提供支援")