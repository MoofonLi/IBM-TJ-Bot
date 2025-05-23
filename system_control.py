import streamlit as st
import os
from dotenv import load_dotenv
import time

from utils.watson_assistant import WatsonAssistant
from utils.text_to_speech import TextToSpeech
from utils.speech_to_text import SpeechToText
from utils.hardware_control import HardwareControl

from tests.hardware_test import test_hardware
from tests.led_test import test_led
from tests.record_test import test_record
from tests.watson_assistant_function_tester import test_watson



load_dotenv()

class SystemControl:
    
    def initialize_system():
        """初始化系統"""
        try:
            # 測試 Watson Assistant
            st.session_state.assistant = WatsonAssistant(
                os.getenv('ASSISTANT_APIKEY'),
                os.getenv('ASSISTANT_URL'),
                os.getenv('ASSISTANT_ID'),
                version='2023-04-15'
            )
            
            # 測試 Text to Speech
            st.session_state.tts = TextToSpeech(
                os.getenv('TTS_APIKEY'),
                os.getenv('TTS_URL')
            )
            
            # 測試 Speech to Text
            st.session_state.stt = SpeechToText(
                os.getenv('STT_APIKEY'),
                os.getenv('STT_URL')
            )
            
            st.session_state.hardware = HardwareControl()
            st.session_state.hardware.lower_arm()

            return True

        except Exception as e:
            return False
        

    def test_system():
        """測試系統"""
        try:
            test_hardware()
            test_led()
            test_record()
            test_watson()
            return True

        except Exception as e:
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
        
        if st.session_state.stt:
            try:
                st.session_state.stt.stop_microphone()
            except:
                pass
        
        # 重置狀態
        st.session_state.assistant = None
        st.session_state.tts = None
        st.session_state.stt = None
        st.session_state.hardware = None
        return True