import sounddevice as sd
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        self.input_device_index = None
        self.sample_rate = None
        self._find_usb_microphone()

    def _find_usb_microphone(self):
        """自動尋找 USB PnP Sound Device 麥克風"""
        devices = sd.query_devices()
        print("錄音裝置列表")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"{i}: {d['name']}")

        # 自動尋找 USB PnP Sound Device
        for i, device in enumerate(devices):
            if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                self.input_device_index = i
                self.sample_rate = int(device['default_samplerate'])
                print(f"已自動選擇錄音裝置: {device['name']} (index {i})")
                print(f"採樣率: {self.sample_rate}")
                return

        print("未找到 USB 麥克風，使用預設錄音裝置")
        self.input_device_index = None
        self.sample_rate = 44100  # 預設採樣率

    def start_microphone(self):
        """檢查麥克風是否準備好"""
        try:
            if self.input_device_index is not None:
                print("麥克風已準備好")
                return True
            else:
                print("未找到指定的麥克風")
                return False
        except Exception as e:
            print(f"麥克風準備失敗: {e}")
            return False

    def listen(self):
        """從麥克風捕獲語音並返回轉錄結果"""
        try:
            duration = 5  # 錄音秒數
            print("開始錄音...")
            
            # 使用與您的測試程式相同的參數
            recording = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype='int16', 
                device=self.input_device_index
            )
            sd.wait()
            print("錄音結束")

            # 將錄音資料轉換為 bytes
            audio_data = recording.tobytes()

            # 傳送音訊到 IBM Watson Speech to Text
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type=f'audio/l16; rate={self.sample_rate}; channels=1',
                model='en-US_BroadbandModel',
            ).get_result()

            # 提取轉錄文本
            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(f"You said: {transcript}")
                return transcript
            else:
                print("No speech detected.")
                return ""
        except Exception as e:
            print(f"Error during Speech to Text: {e}")
            return ""

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
            print(f"語音識別錯誤: {e}")
            return ""

    def stop_microphone(self):
        """停止麥克風（sounddevice 不需要特別處理）"""
        print("麥克風已停止")