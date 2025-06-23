import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import threading
import time
import queue

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        
        # 新增狀態管理
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.input_device_index = None
        self.sample_rate = 44100  # 預設採樣率
        
    def find_microphone(self):
        """尋找並設定麥克風設備"""
        devices = sd.query_devices()
        print("錄音裝置列表:")
        
        # 列出所有輸入設備
        input_devices = []
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"{i}: {d['name']} - 採樣率: {d['default_samplerate']}")
                input_devices.append((i, d))
        
        # 優先尋找 USB 麥克風
        for i, device in input_devices:
            if "USB PnP Sound Device" in device['name']:
                self.input_device_index = i
                self.sample_rate = int(device['default_samplerate'])
                print(f"已選擇 USB 麥克風: {device['name']} (index {i})")
                return True
        
        # 如果沒有 USB 麥克風，使用預設輸入設備
        if input_devices:
            default_input = sd.default.device[0]
            if default_input is not None and default_input >= 0:
                self.input_device_index = default_input
                self.sample_rate = int(devices[default_input]['default_samplerate'])
                print(f"使用預設麥克風: {devices[default_input]['name']}")
                return True
        
        print("錯誤：找不到可用的麥克風設備")
        return False

    def audio_callback(self, indata, frames, time, status):
        """音訊回調函數，用於即時錄音"""
        if status:
            print(f"錄音狀態警告: {status}")
        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self):
        """開始錄音（非阻塞）"""
        if not self.find_microphone():
            return False
            
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        try:
            # 使用 InputStream 進行即時錄音
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                device=self.input_device_index,
                callback=self.audio_callback,
                blocksize=1024
            )
            self.stream.start()
            print("開始錄音...")
            return True
        except Exception as e:
            print(f"開始錄音時發生錯誤: {e}")
            self.is_recording = False
            return False

    def stop_recording(self):
        """停止錄音並回傳識別結果"""
        if not self.is_recording:
            return ""
            
        self.is_recording = False
        time.sleep(0.2)  # 等待最後的音訊數據
        
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass
        
        print("錄音結束，處理音訊...")
        
        # 從 queue 收集所有音訊數據
        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())
        
        if not audio_chunks:
            print("沒有錄到音訊")
            return ""
        
        # 合併音訊數據
        audio_data = np.concatenate(audio_chunks, axis=0)
        
        # 轉換為 int16
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # 儲存為臨時檔案
        filename = "temp_recording.wav"
        wavfile.write(filename, self.sample_rate, audio_data)
        
        # 檢查檔案
        file_size = os.path.getsize(filename)
        print(f"錄音檔案大小: {file_size} bytes")
        
        if file_size < 1000:
            print("警告：錄音檔案太小，可能沒有錄到聲音")
            return ""
        
        # 進行語音識別
        try:
            with open(filename, 'rb') as audio_file:
                result = self.speech_to_text.recognize(
                    audio=audio_file,
                    content_type='audio/wav',
                    model='en-US_BroadbandModel',
                ).get_result()
            
            # 清理臨時檔案
            os.remove(filename)
            
            # 提取文字
            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(f"識別結果: {transcript}")
                return transcript
            else:
                print("沒有識別到語音")
                return ""
                
        except Exception as e:
            print(f"語音識別錯誤: {e}")
            return ""

    def listen(self):
        """保留舊方法的相容性 - 固定時長錄音"""
        if self.start_recording():
            time.sleep(5)  # 錄音 5 秒
            return self.stop_recording()
        return ""

    def start_microphone(self):
        """檢查麥克風是否準備好"""
        return self.find_microphone()
        
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