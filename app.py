import streamlit as st
from dotenv import load_dotenv
from src.system_control import SystemControl
import time

def agent_responce(prompt, agent_type):
    if agent_type == "main_agent":
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            # 使用 streaming 生成回應
            full_response = ""
            
            for response_chunk in st.session_state.chat_setting.generate_response_stream(prompt,agent_type):
                full_response = response_chunk
                # 即時更新顯示的內容
                message_placeholder.markdown(full_response + "▌")  # 加上游標效果
            
            # 移除游標，顯示最終結果
            message_placeholder.markdown(full_response)
            st.session_state.chat_history.append(("assistant", full_response))
    else:
        full_response = ""
        
        for response_chunk in st.session_state.chat_setting.generate_response_stream(prompt,agent_type):
            full_response = response_chunk
        
    return full_response


def process_message(user_input):
    """處理使用者訊息並執行相應動作"""
    if not st.session_state.assistant:
        st.error("服務尚未初始化！")
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

        if intents and len(intents) > 0 and intents[0]['intent'] == "ask_weather":
            bot_reply = agent_responce(agent_responce(user_input, "weather"), "main_agent")
            st.session_state.hardware.shine("blue")
            time.sleep(3)
            st.session_state.hardware.shine("off")
        elif intents and len(intents) > 0 and intents[0]['intent'] == "search_online":
            bot_reply = agent_responce(agent_responce(user_input, "google_search"), "main_agent")
            st.session_state.hardware.shine("white")
            time.sleep(3)
            st.session_state.hardware.shine("off")
            
        else:
            # 像原始代碼一樣逐條處理回應文字
            for text in response_texts:
                if text['response_type'] == 'text':
                    bot_reply = text['text']

                    if bot_reply == "Chat":
                        bot_reply = agent_responce(user_input, "main_agent")
                        st.session_state.hardware.wave()
                    
                    else:                
                        # 保存對話歷史 - 機器人回應
                        st.session_state.chat_history.append(("assistant", bot_reply))

                        # 顯示於chat介面
                        st.chat_message("assistant").write(bot_reply)

                    
        # 語音輸出 - 直接在TJBot上播放
        if st.session_state.tts:
            st.session_state.tts.speak(bot_reply)

        
        # 執行硬體動作
        if intents and len(intents) > 0:
            top_intent = intents[0]['intent']
            if top_intent == 'wave':
                st.session_state.hardware.wave()
                st.info("瓦麥揮手👋")
            elif top_intent == 'lower-arm':
                st.session_state.hardware.lower_arm()
                st.info("瓦麥放下手臂🙇")
            elif top_intent == 'raise-arm':
                st.session_state.hardware.raise_arm()
                st.info("瓦麥舉起手臂🙋‍♂️")
            elif top_intent == 'shine':
                # 從 entities 提取顏色
                color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                st.session_state.hardware.shine(color)
                st.info(f"瓦麥發光: {color}✨")
            elif top_intent == 'dance':
                st.session_state.hardware.dance()
                st.info("瓦麥跳舞🕺")

        return "處理完成"
    else:
        st.error("無法獲取 Assistant 回應")
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
    page_title="TJBot Control Web",
    page_icon="🤖",
    layout="wide"
    )

    # 側邊欄
    with st.sidebar:

        # 硬體控制
        st.header("硬體控制")

        if st.button("初始化系統", use_container_width=True):
                with st.spinner("正在初始化系統..."):
                    if SystemControl.initialize_system():
                        st.success("系統已初始化")
                    else:
                        st.error("系統初始化失敗")

        if st.button("關閉系統", use_container_width=True):
                with st.spinner("正在關閉系統..."):
                    if SystemControl.shutdown_system():
                        st.success("系統已關閉")
                    else:
                        st.error("系統關閉失敗")
                        
        # 燈光控制
        colors = ["off", "red", "green", "blue", "white", "yellow", "purple", "orange"]
        color = st.selectbox("選擇燈光顏色", colors)
        if color:
            if st.session_state.hardware:
                st.session_state.hardware.shine(color)       

        # 動作控制
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
        st.header("聊天控制")
        if 'is_recording' not in st.session_state:
            st.session_state.is_recording = False

        # 語音輸入控制
        st.header("🎤 語音控制")
        
        # 使用不同的按鈕顯示來表示狀態
        if st.session_state.is_recording:
            if st.button("🔴 停止錄音", use_container_width=True, type="secondary"):
                st.session_state.is_recording = False
                if st.session_state.stt:
                    with st.spinner("正在處理語音..."):
                        user_input = st.session_state.stt.listen()
                        if user_input and user_input.strip():
                            # 保存到對話歷史
                            st.session_state.chat_history.append(("user", user_input))
                            # 處理訊息
                            process_message(user_input)
                            st.experimental_rerun()
                        else:
                            st.warning("沒有識別到語音，請重試")
                            st.experimental_rerun()
                else:
                    st.error("語音系統未初始化")
        else:
            if st.button("🎤 開始語音輸入", use_container_width=True, type="primary"):
                if st.session_state.stt:
                    st.session_state.is_recording = True
                    if st.session_state.stt.start_microphone():
                        st.info("🎤 正在錄音，請說話... (5秒後自動結束)")
                        st.experimental_rerun()
                    else:
                        st.error("無法啟動麥克風")
                        st.session_state.is_recording = False
                else:
                    st.error("請先初始化系統")

        # 顯示錄音狀態
        if st.session_state.is_recording:
            st.info("🔴 錄音中...")

        # 清除對話按鈕
        if st.button("清除對話", use_container_width=True):
            st.session_state.chat_history = []
            st.experimental_rerun()


    # 主要區域 - 聊天介面
    st.header("聊天&對話")
        
    # 顯示聊天歷史
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.chat_message("user").write(message)
        else:
            st.chat_message("assistant").write(message)

    # 文字輸入
    user_input = st.chat_input("請輸入訊息或使用左側語音按鈕...")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        st.chat_message("user").write(user_input)
        process_message(user_input)


if __name__ == "__main__": 
    main()