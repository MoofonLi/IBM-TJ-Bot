import streamlit as st
from dotenv import load_dotenv
import asyncio
from system_control import SystemControl


def process_message(user_input):
    """處理使用者訊息並執行相應動作"""
    if not st.session_state.assistant:
        st.error("服務尚未初始化！請先測試系統")
        return
    
    if not user_input or user_input.strip() == "":
        st.warning("請輸入有效訊息")
        return
    
    # 發送到 Watson Assistant
    response = st.session_state.assistant.send_message(user_input)
    
    if response:
        # 處理回應
        intents = response.get('output', {}).get('intents', [])
        entities = response.get('output', {}).get('entities', [])
        response_texts = response.get('output', {}).get('generic', [])
        
        # 保存對話歷史 - 用戶輸入
        st.session_state.chat_history.append(("user", user_input))
        
        # 像原始代碼一樣逐條處理回應文字
        for text in response_texts:
            if text['response_type'] == 'text':
                bot_reply = text['text']
                
                # 保存對話歷史 - 機器人回應
                st.session_state.chat_history.append(("assistant", bot_reply))

                # 顯示於chat介面
                st.chat_message("user").write(user_input)
                st.chat_message("assistant").write(bot_reply)
                
                # 語音輸出 - 直接在TJBot上播放
                if st.session_state.tts:
                    st.session_state.tts.speak(bot_reply)

        
        # 執行硬體動作
        if intents and len(intents) > 0:
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
                # 從 entities 提取顏色
                color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                st.session_state.hardware.shine(color)
                st.info(f"機器人發光: {color}✨")

        return "處理完成"
    else:
        st.error("無法獲取 Watson 回應")
        return None



def main():
    load_dotenv()

    # Initial Session State
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

    # 網頁標題配置
    st.set_page_config(
    page_title="TJBot 控制台",
    page_icon="🤖",
    layout="wide"
    )

    # 主要介面
    st.title("🤖 TJBot 控制台")
    st.write("透過文字或語音與 TJBot 互動")

    # 側邊欄
    with st.sidebar:

        # 硬體控制
        st.header("硬體控制")

        # if st.button("測試系統"):
        #         with st.spinner("正在測試系統..."):
        #             if SystemControl.test_system():
        #                 st.success("系統測試通過！")
        #             else:
        #                 st.error("系統測試失敗")

        if st.button("初始化系統"):
                with st.spinner("正在初始化系統..."):
                    if SystemControl.initialize_system():
                        st.success("系統初始化通過！")
                    else:
                        st.error("系統初始化失敗")

        if st.button("關閉系統"):
                with st.spinner("正在關閉系統..."):
                    if SystemControl.shutdown_system():
                        st.success("系統已安全關閉")
                    else:
                        st.error("系統關閉失敗")
                        
        # 燈光控制
        colors = ["red", "green", "blue", "white", "yellow", "purple", "orange" "off"]
        color = st.selectbox("選擇燈光顏色", colors)
        if color:
            if st.session_state.hardware:
                st.session_state.hardware.shine(color)       

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👋 揮手"):
                if st.session_state.hardware:
                    st.session_state.hardware.wave()
            
            if st.button("🙋‍♂️ 舉手"):
                if st.session_state.hardware:
                    st.session_state.hardware.raise_arm()

        with col2:
            if st.button("🙇 放下手"):
                if st.session_state.hardware:
                    st.session_state.hardware.lower_arm()
                    

            if st.button("🕺 跳舞"):
                if st.session_state.hardware:
                    st.session_state.hardware.dance()

        # 語音輸入按鈕
        st.header("語音輸入")
        if 'is_recording' not in st.session_state:
            st.session_state.is_recording = False

        if st.button("🎤 按此開始/停止語音輸入", use_container_width=True):
            st.session_state.is_recording = not st.session_state.is_recording
            if st.session_state.is_recording:
                st.session_state.is_recording = True
                st.info("正在聆聽，請說話...")
                st.session_state.stt.start_microphone()
            else:
                st.session_state.is_recording = False
                st.info("錄音已停止，正在處理...")
                if st.session_state.stt:
                    user_input = st.session_state.stt.listen().strip()
                    process_message(user_input)

    # 主要區域 - 聊天介面
    st.header("聊天對話")

    # 聊天歷史控制
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("清除對話"):
            st.session_state.chat_history = []
            st.rerun()

    # 顯示聊天歷史
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.chat_message("user").write(message)
        else:
            st.chat_message("assistant").write(message)

    # 文字輸入
    user_input = st.chat_input("請輸入訊息或使用左側語音按鈕...")

    if user_input:
        with st.spinner("處理中..."):
            process_message(user_input)


    # 頁腳
    st.markdown("---")
    st.markdown("TJBot 控制台 - 由 IBM Watson AI 支援")



if __name__ == "__main__": 
    main()