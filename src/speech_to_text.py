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
        """尋找並設定麥克風設備 - 參考 audio_device_test.py 實現"""
        devices = sd.query_devices()
        print("錄音裝置列表:")
        
        # 列出所有輸入設備
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"{i}: {d['name']}")
        
        # 自動尋找 USB PnP Sound Device (麥克風)
        input_index = None
        for i, device in enumerate(devices):
            if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                input_index = i
                print(f"已自動選擇錄音裝置: {device['name']} (index {i})")
                break
        
        if input_index is None:
            print("沒有找到 USB 麥克風，請確認是否插好。")
            return False
        
        # 設定錄音參數
        self.input_device_index = input_index
        self.sample_rate = int(devices[input_index]['default_samplerate'])
        
        return True

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
        """簡化的錄音方法 - 參考 audio_device_test.py 的直接錄音方式"""
        # 參數設定
        duration = 5  # 錄音秒數
        filename = "temp_recording.wav"
        
        # 尋找麥克風設備
        if not self.find_microphone():
            return ""
        
        print("開始錄音")
        try:
            # 直接錄音 - 參考 audio_device_test.py 的方式
            recording = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype='int16', 
                device=self.input_device_index
            )
            sd.wait()
            print("錄音結束")
            
            # 儲存成 wav
            wavfile.write(filename, self.sample_rate, recording)
            print(f"錄音已儲存為 {filename}")
            
            # 檢查檔案大小
            file_size = os.path.getsize(filename)
            print(f"錄音檔案大小: {file_size} bytes")
            
            if file_size < 1000:
                print("警告：錄音檔案太小，可能沒有錄到聲音")
                return ""
            
            # 進行語音識別
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
            print(f"錄音或識別錯誤: {e}")
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