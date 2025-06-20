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
        self.sample_rate = 44100
        
    def start_microphone(self):
        """尋找並設定 USB 麥克風"""
        try:
            # 列出所有音訊設備
            devices = sd.query_devices()
            
            # 自動尋找 USB PnP Sound Device (你的麥克風)
            self.input_device_index = None
            for i, device in enumerate(devices):
                if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                    self.input_device_index = i
                    # 使用設備的預設採樣率
                    self.sample_rate = int(device['default_samplerate'])
                    print(f"已選擇錄音裝置: {device['name']} (index {i})")
                    print(f"採樣率: {self.sample_rate}")
                    return True
            
            # 如果沒找到 USB PnP Sound Device，列出所有可用的輸入設備
            if self.input_device_index is None:
                print("沒有找到 USB PnP Sound Device，可用的錄音設備：")
                for i, device in enumerate(devices):
                    if device['max_input_channels'] > 0:
                        print(f"{i}: {device['name']}")
                
                # 使用預設輸入設備
                self.input_device_index = sd.default.device[0]
                print(f"使用預設錄音設備 (index {self.input_device_index})")
                return True
                
        except Exception as e:
            print(f"Error setting up microphone: {e}")
            return False

    def listen(self, duration=5):
        """從麥克風捕獲語音並返回轉錄結果"""
        if self.input_device_index is None:
            print("麥克風未初始化，請先呼叫 start_microphone()")
            return ""
        
        try:
            print(f"開始錄音 {duration} 秒...")
            
            # 使用 sounddevice 錄音
            recording = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype='int16', 
                device=self.input_device_index
            )
            sd.wait()  # 等待錄音完成
            
            print("錄音結束，正在處理...")
            
            # 將 numpy array 轉換為 bytes
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
        """停止麥克風（sounddevice 不需要手動停止）"""
        print("麥克風已停止")
        pass

    def test_recording(self, duration=3):
        """測試錄音功能"""
        if not self.start_microphone():
            return False
            
        print("測試錄音...")
        result = self.listen(duration)
        print(f"測試結果: {result}")
        return True