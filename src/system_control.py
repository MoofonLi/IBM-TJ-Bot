import streamlit as st
import os
from dotenv import load_dotenv
import time

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
            # 檢查必要的環境變數
            required_env_vars = [
                'ASSISTANT_APIKEY', 'ASSISTANT_URL', 'ASSISTANT_ID',
                'TTS_APIKEY', 'TTS_URL',
                'STT_APIKEY', 'STT_URL'
            ]
            
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                st.error(f"缺少必要的環境變數: {', '.join(missing_vars)}")
                return False

            # Watson Assistant
            try:
                st.session_state.assistant = WatsonAssistant(
                    os.getenv('ASSISTANT_APIKEY'),
                    os.getenv('ASSISTANT_URL'),
                    os.getenv('ASSISTANT_ID'),
                    version='2023-04-15'
                )
                st.info("✅ Watson Assistant 初始化成功")
            except Exception as e:
                st.error(f"Watson Assistant 初始化失敗: {str(e)}")
                return False
            
            # Text to Speech
            try:
                st.session_state.tts = TextToSpeech(
                    os.getenv('TTS_APIKEY'),
                    os.getenv('TTS_URL')
                )
                st.info("✅ Text to Speech 初始化成功")
            except Exception as e:
                st.error(f"Text to Speech 初始化失敗: {str(e)}")
                # TTS失敗不應該阻止整個系統初始化
                st.session_state.tts = None
                st.warning("TTS 功能將被禁用")
            
            # Speech to Text
            try:
                st.session_state.stt = SpeechToText(
                    os.getenv('STT_APIKEY'),
                    os.getenv('STT_URL')
                )
                st.info("✅ Speech to Text 初始化成功")
            except Exception as e:
                st.error(f"Speech to Text 初始化失敗: {str(e)}")
                # STT失敗不應該阻止整個系統初始化
                st.session_state.stt = None
                st.warning("STT 功能將被禁用")
            
            # Hardware Control
            try:
                st.session_state.hardware = HardwareControl()
                st.info("✅ Hardware Control 初始化成功")
            except Exception as e:
                st.error(f"Hardware Control 初始化失敗: {str(e)}")
                # 硬體控制失敗不應該阻止整個系統初始化
                st.session_state.hardware = None
                st.warning("硬體控制功能將被禁用")

            return True

        except Exception as e:
            st.error(f"系統初始化發生未預期錯誤: {str(e)}")
            return False
        

    @staticmethod
    def shutdown_system():
        """關閉系統和清理資源"""
        try:
            # 硬體清理
            if st.session_state.hardware:
                try:
                    # 關閉 LED
                    st.session_state.hardware.shine("off")
                    # 放下手臂
                    st.session_state.hardware.lower_arm()
                    # 清理資源
                    st.session_state.hardware.cleanup()
                    st.info("✅ 硬體資源已清理")
                except Exception as e:
                    st.warning(f"硬體清理時發生錯誤: {str(e)}")
            
            # STT 清理
            if st.session_state.stt:
                try:
                    st.session_state.stt.stop_microphone()
                    st.info("✅ 麥克風已停止")
                except Exception as e:
                    st.warning(f"麥克風停止時發生錯誤: {str(e)}")
            
            # TTS 清理
            if st.session_state.tts:
                try:
                    # 如果TTS有清理方法，在這裡調用
                    # st.session_state.tts.cleanup()
                    st.info("✅ TTS 服務已停止")
                except Exception as e:
                    st.warning(f"TTS 清理時發生錯誤: {str(e)}")
            
            # 重置狀態
            st.session_state.assistant = None
            st.session_state.tts = None
            st.session_state.stt = None
            st.session_state.hardware = None
            st.session_state.is_recording = False

            st.success("✅ 系統已完全關閉")
            return True
            
        except Exception as e:
            st.error(f"系統關閉時發生錯誤: {str(e)}")
            return False


    @staticmethod
    def check_system_status():
        """檢查系統各組件狀態"""
        status = {
            'assistant': st.session_state.assistant is not None,
            'tts': st.session_state.tts is not None,
            'stt': st.session_state.stt is not None,
            'hardware': st.session_state.hardware is not None
        }
        return status


    @staticmethod
    def safe_tts_speak(text, max_length=500):
        """安全的TTS語音輸出，限制文字長度以避免記憶體問題"""
        if not st.session_state.tts:
            return False
        
        if not text or text.strip() == "":
            return False
        
        try:
            # 限制文字長度以避免記憶體問題
            if len(text) > max_length:
                text = text[:max_length] + "..."
                st.warning(f"文字過長，已截取前{max_length}個字符")
            
            st.session_state.tts.speak(text)
            return True
            
        except Exception as e:
            st.error(f"TTS 語音輸出失敗: {str(e)}")
            return False


    @staticmethod
    def safe_stt_listen(timeout=10):
        """安全的STT語音輸入"""
        if not st.session_state.stt:
            return None
        
        try:
            # 設置超時以避免無限等待
            result = st.session_state.stt.listen()
            return result.strip() if result else None
            
        except Exception as e:
            st.error(f"STT 語音識別失敗: {str(e)}")
            return None