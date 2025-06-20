import streamlit as st
import os
from dotenv import load_dotenv
import time
import traceback

from src.watson_assistant import WatsonAssistant
from src.text_to_speech import TextToSpeech
from src.speech_to_text import SpeechToText
from src.hardware_control import HardwareControl


load_dotenv()

class SystemControl:
    
    @staticmethod
    def initialize_system():
        """初始化系統"""
        try:
            # 先重置所有session state
            st.session_state.assistant = None
            st.session_state.tts = None
            st.session_state.stt = None
            st.session_state.hardware = None

            # 1. Watson Assistant
            print("正在初始化 Watson Assistant...")
            st.session_state.assistant = WatsonAssistant(
                os.getenv('ASSISTANT_APIKEY'),
                os.getenv('ASSISTANT_URL'),
                os.getenv('ASSISTANT_ID'),
                version='2023-04-15'
            )
            print("Watson Assistant 初始化完成")
            
            # 2. Text to Speech
            print("正在初始化 Text to Speech...")
            st.session_state.tts = TextToSpeech(
                os.getenv('TTS_APIKEY'),
                os.getenv('TTS_URL')
            )
            print("Text to Speech 初始化完成")
            
            # 3. Speech to Text
            print("正在初始化 Speech to Text...")
            st.session_state.stt = SpeechToText(
                os.getenv('STT_APIKEY'),
                os.getenv('STT_URL')
            )
            print("Speech to Text 初始化完成")
            
            # 4. Hardware Control
            print("正在初始化 Hardware Control...")
            st.session_state.hardware = HardwareControl()
            print("Hardware Control 初始化完成")

            print("系統初始化完成！")
            return True

        except Exception as e:
            print(f"系統初始化失敗: {e}")
            print(f"錯誤詳細資訊: {traceback.format_exc()}")
            
            # 清理已初始化的資源
            SystemControl.cleanup_partial_init()
            return False
        
    @staticmethod
    def cleanup_partial_init():
        """清理部分初始化的資源"""
        try:
            if hasattr(st.session_state, 'hardware') and st.session_state.hardware:
                st.session_state.hardware.cleanup()
            if hasattr(st.session_state, 'stt') and st.session_state.stt:
                st.session_state.stt.stop_microphone()
        except:
            pass
        
        st.session_state.assistant = None
        st.session_state.tts = None
        st.session_state.stt = None
        st.session_state.hardware = None

    @staticmethod
    def shutdown_system():
        """關閉系統和清理資源"""
        try:
            if hasattr(st.session_state, 'hardware') and st.session_state.hardware:
                # 關閉 LED
                st.session_state.hardware.shine("off")
                # 放下手臂
                st.session_state.hardware.lower_arm()
                # 清理資源
                st.session_state.hardware.cleanup()
            
            if hasattr(st.session_state, 'stt') and st.session_state.stt:
                try:
                    st.session_state.stt.stop_microphone()
                except:
                    pass
            
            # 重置狀態
            st.session_state.assistant = None
            st.session_state.tts = None
            st.session_state.stt = None
            st.session_state.hardware = None

            print("系統已安全關閉")
            return True
            
        except Exception as e:
            print(f"系統關閉時發生錯誤: {e}")
            return False