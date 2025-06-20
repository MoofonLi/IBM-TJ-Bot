import pyaudio
import sounddevice as sd
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.input_device_index = None
        self.sample_rate = None
        self._detect_audio_device()

    def _detect_audio_device(self):
        """自動偵測音頻設備"""
        try:
            devices = sd.query_devices()
            print("搜尋音頻設備...")
            
            # 尋找 USB PnP Sound Device (麥克風)
            for i, device in enumerate(devices):
                if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                    self.input_device_index = i
                    self.sample_rate = int(device['default_samplerate'])
                    print(f"找到錄音設備: {device['name']} (index {i}, 採樣率: {self.sample_rate})")
                    return True
            
            # 如果沒找到 USB PnP，尋找其他可用的輸入設備
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    self.input_device_index = i
                    self.sample_rate = int(device['default_samplerate'])
                    print(f"使用備用錄音設備: {device['name']} (index {i}, 採樣率: {self.sample_rate})")
                    return True
                    
            print("未找到可用的錄音設備")
            return False
            
        except Exception as e:
            print(f"設備偵測錯誤: {e}")
            # 使用預設設定
            self.input_device_index = 1
            self.sample_rate = 44100
            return False

    def start_microphone(self):
        """啟動麥克風"""
        if self.input_device_index is None:
            print("錯誤: 未找到可用的錄音設備")
            return False
            
        try:
            # 計算適當的 buffer size
            buffer_size = 4096
            if self.sample_rate < 22050:
                buffer_size = 2048
            elif self.sample_rate > 48000:
                buffer_size = 8192
                
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=buffer_size
            )
            print(f"麥克風已啟動 (設備: {self.input_device_index}, 採樣率: {self.sample_rate})")
            return True
        except Exception as e:
            print(f"啟動麥克風失敗: {e}")
            return False

    def listen(self, duration=5):
        """從麥克風捕獲語音並返回轉錄結果"""
        if not self.stream:
            print("錯誤: 麥克風未啟動")
            return ""
            
        try:
            print(f"開始錄音 {duration} 秒...")
            frames = []
            
            # 根據採樣率計算需要讀取的 frames 數量
            buffer_size = self.stream._frames_per_buffer
            total_frames = int(self.sample_rate / buffer_size * duration)
            
            for _ in range(total_frames):
                data = self.stream.read(buffer_size, exception_on_overflow=False)
                frames.append(data)

            audio_data = b''.join(frames)
            print("錄音完成，開始轉換...")

            # 傳送音訊到 IBM Watson Speech to Text
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type=f'audio/l16; rate={self.sample_rate}; channels=1',
                model='en-US_BroadbandModel',
            ).get_result()

            # 提取轉錄文本
            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(f"辨識結果: {transcript}")
                return transcript
            else:
                print("未偵測到語音")
                return ""
                
        except Exception as e:
            print(f"語音轉文字錯誤: {e}")
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
        """關閉麥克風流"""
        try:
            if self.stream and not self.stream.is_stopped():
                self.stream.stop_stream()
                self.stream.close()
                print("麥克風已關閉")
        except Exception as e:
            print(f"關閉麥克風錯誤: {e}")
        finally:
            if hasattr(self, 'audio'):
                self.audio.terminate()