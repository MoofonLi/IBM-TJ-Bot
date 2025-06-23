import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import threading
import time
import queue
import uuid

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        
        # 錄音相關變數
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.input_device = None
        self.sample_rate = 16000  # 固定採樣率，避免每次查詢
        
        # 初始化時就設定麥克風
        self._initialize_microphone()
    
    def _initialize_microphone(self):
        """初始化時設定麥克風，避免每次都重新查詢"""
        try:
            devices = sd.query_devices()
            print("可用的錄音裝置:")
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"{i}: {device['name']} (channels: {device['max_input_channels']})")
                    
                    # 尋找 USB 麥克風
                    if "USB PnP Sound Device" in device['name']:
                        self.input_device = i
                        self.sample_rate = int(device['default_samplerate'])
                        print(f"✅ 已選擇麥克風: {device['name']} (index {i}, rate {self.sample_rate})")
                        return True
            
            # 如果沒找到指定麥克風，使用預設
            if self.input_device is None:
                self.input_device = sd.default.device[0]  # 預設輸入裝置
                print(f"⚠️  使用預設麥克風 (index {self.input_device})")
                
        except Exception as e:
            print(f"初始化麥克風失敗: {e}")
            return False
        
        return True
    
    def start_recording(self):
        """開始錄音 - 真正的開始/停止控制"""
        if self.is_recording:
            print("已經在錄音中...")
            return False
            
        if self.input_device is None:
            print("麥克風未初始化!")
            return False
        
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        # 開始錄音執行緒
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()
        
        print("🎤 開始錄音...")
        return True
    
    def stop_recording(self):
        """停止錄音並回傳識別結果"""
        if not self.is_recording:
            print("目前沒有在錄音")
            return ""
        
        print("⏹️  停止錄音...")
        self.is_recording = False
        
        # 等待錄音執行緒結束
        if self.recording_thread:
            self.recording_thread.join(timeout=2)
        
        # 處理錄音資料
        return self._process_recorded_audio()
    
    def _record_audio(self):
        """錄音執行緒 - 持續錄音直到停止"""
        try:
            # 使用較小的 chunk 來實現即時控制
            chunk_duration = 0.1  # 0.1 秒一個 chunk
            chunk_size = int(self.sample_rate * chunk_duration)
            
            with sd.InputStream(
                device=self.input_device,
                channels=1,
                samplerate=self.sample_rate,
                dtype='int16',
                blocksize=chunk_size
            ) as stream:
                
                while self.is_recording:
                    audio_chunk, overflowed = stream.read(chunk_size)
                    if not overflowed:
                        self.audio_queue.put(audio_chunk)
                    time.sleep(0.01)  # 小延遲避免 CPU 過載
                        
        except Exception as e:
            print(f"錄音執行緒錯誤: {e}")
            self.is_recording = False
    
    def _process_recorded_audio(self):
        """處理錄音資料並進行語音識別"""
        try:
            # 收集所有音訊 chunks
            audio_chunks = []
            while not self.audio_queue.empty():
                chunk = self.audio_queue.get()
                audio_chunks.append(chunk)
            
            if not audio_chunks:
                print("沒有錄到音訊資料")
                return ""
            
            # 合併所有 chunks
            full_audio = np.concatenate(audio_chunks, axis=0)
            full_audio = np.squeeze(full_audio)
            
            # 檢查音訊長度
            duration = len(full_audio) / self.sample_rate
            print(f"錄音時長: {duration:.2f} 秒")
            
            if duration < 0.5:
                print("錄音時間太短，可能沒有有效語音")
                return ""
            
            # 使用唯一檔名避免衝突
            filename = f"temp_recording_{uuid.uuid4().hex[:8]}.wav"
            
            try:
                # 儲存檔案
                wavfile.write(filename, self.sample_rate, full_audio)
                file_size = os.path.getsize(filename)
                print(f"音訊檔案大小: {file_size} bytes")
                
                if file_size > 1000:  # 檔案大小檢查
                    # 進行語音識別
                    with open(filename, 'rb') as audio_file:
                        result = self.speech_to_text.recognize(
                            audio=audio_file,
                            content_type='audio/wav',
                            model='en-US_BroadbandModel',
                        ).get_result()
                    
                    # 提取結果
                    if 'results' in result and len(result['results']) > 0:
                        transcript = result['results'][0]['alternatives'][0]['transcript']
                        print(f"🗣️  識別結果: {transcript}")
                        return transcript.strip()
                    else:
                        print("沒有識別到語音內容")
                        return ""
                else:
                    print("音訊檔案太小")
                    return ""
                    
            finally:
                # 清理臨時檔案
                try:
                    os.remove(filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"處理錄音時發生錯誤: {e}")
            return ""
    
    def quick_record(self, duration=5):
        """快速錄音模式 - 固定時間錄音（保留原有功能）"""
        try:
            if self.input_device is None:
                print("麥克風未初始化!")
                return ""
            
            print(f"🎤 開始 {duration} 秒錄音...")
            
            # 直接錄音指定時間
            recording = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype='int16', 
                device=self.input_device
            )
            sd.wait()  # 等待錄音完成
            
            print("⏹️  錄音完成")
            
            # 使用唯一檔名
            filename = f"temp_quick_record_{uuid.uuid4().hex[:8]}.wav"
            
            try:
                recording_squeezed = np.squeeze(recording)
                wavfile.write(filename, self.sample_rate, recording_squeezed)
                
                file_size = os.path.getsize(filename)
                print(f"檔案大小: {file_size} bytes")
                
                if file_size > 1000:
                    with open(filename, 'rb') as audio_file:
                        result = self.speech_to_text.recognize(
                            audio=audio_file,
                            content_type='audio/wav',
                            model='en-US_BroadbandModel',
                        ).get_result()
                    
                    if 'results' in result and len(result['results']) > 0:
                        transcript = result['results'][0]['alternatives'][0]['transcript']
                        print(f"🗣️  識別結果: {transcript}")
                        return transcript.strip()
                    else:
                        print("沒有識別到語音內容")
                        return ""
                else:
                    print("錄音檔案太小")
                    return ""
                    
            finally:
                try:
                    os.remove(filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"快速錄音錯誤: {e}")
            return ""
    
    # 保持向後相容
    def start_microphone(self):
        return self.start_recording()
    
    def listen(self):
        return self.quick_record()
    
    def stop_microphone(self):
        return self.stop_recording()