import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os

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
        """從麥克風捕獲語音，先存檔再識別"""
        try:
            duration = 5  # 錄音秒數
            filename = "temp_recording.wav"
            
            print("開始錄音...")
            
            # 使用與您的測試程式完全相同的錄音邏輯
            recording = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype='int16', 
                device=self.input_device_index
            )
            sd.wait()
            print("錄音結束")

            # 儲存成 wav 檔案（與您的測試程式相同）
            wavfile.write(filename, self.sample_rate, recording)
            print(f"錄音已儲存為 {filename}")
            
            # 檢查檔案是否存在和大小
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"檔案大小: {file_size} bytes")
                
                if file_size > 1000:  # 如果檔案大於 1KB，應該有錄到聲音
                    print("檔案看起來正常，開始進行語音識別...")
                    
                    # 讀取 wav 檔案並送給 STT
                    with open(filename, 'rb') as audio_file:
                        result = self.speech_to_text.recognize(
                            audio=audio_file,
                            content_type='audio/wav',
                            model='en-US_BroadbandModel',
                        ).get_result()

                    # 提取轉錄文本
                    if 'results' in result and len(result['results']) > 0:
                        transcript = result['results'][0]['alternatives'][0]['transcript']
                        print(f"You said: {transcript}")
                        
                        # 清理臨時檔案
                        os.remove(filename)
                        return transcript
                    else:
                        print("No speech detected.")
                        return ""
                else:
                    print("警告：錄音檔案太小，可能沒有錄到聲音")
                    return ""
            else:
                print("錯誤：錄音檔案未建立")
                return ""
                
        except Exception as e:
            print(f"Error during recording or Speech to Text: {e}")
            # 如果出錯，也要清理臨時檔案
            if os.path.exists("temp_recording.wav"):
                os.remove("temp_recording.wav")
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