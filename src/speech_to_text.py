import sounddevice as sd
import scipy.io.wavfile as wavfile
import tempfile
import os
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class SpeechToText:
    def __init__(self, apikey, url):
        try:
            print(f"初始化 STT - API Key前4碼: {apikey[:4] if apikey else 'None'}...")
            print(f"初始化 STT - URL: {url}")
            
            authenticator = IAMAuthenticator(apikey)
            self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
            self.speech_to_text.set_service_url(url)
            self.input_index = None
            
            # 測試連接
            models = self.speech_to_text.list_models().get_result()
            print(f"STT 連接成功，可用模型數量: {len(models.get('models', []))}")
            
            self._find_microphone()
            print(f"STT 初始化完成，音頻輸入設備索引: {self.input_index}")
            
        except Exception as e:
            print(f"STT 初始化失敗: {e}")
            raise

    def _find_microphone(self):
        """自動尋找可用的音頻輸入設備"""
        try:
            devices = sd.query_devices()
            print(f"偵測到 {len(devices)} 個音頻設備")
            
            # 優先尋找 USB PnP Sound Device
            for i, device in enumerate(devices):
                device_name = str(device.get('name', ''))
                max_input = device.get('max_input_channels', 0)
                
                print(f"設備 {i}: {device_name}, 輸入通道: {max_input}")
                
                if "USB PnP Sound Device" in device_name and max_input > 0:
                    self.input_index = i
                    print(f"找到 USB PnP Sound Device 於索引 {i}")
                    return

            # 如果沒找到 USB PnP Sound Device，使用預設輸入設備
            default_input = sd.query_devices(kind='input')
            if default_input and default_input.get('max_input_channels', 0) > 0:
                # 找到預設輸入設備的索引
                for i, device in enumerate(devices):
                    if device.get('name') == default_input.get('name'):
                        self.input_index = i
                        print(f"使用預設輸入設備: {device.get('name')} (索引 {i})")
                        return
                        
            print("警告: 未找到可用的音頻輸入設備")
            
        except Exception as e:
            print(f"音頻設備檢測錯誤: {e}")
            self.input_index = None

    def start_microphone(self):
        """檢查麥克風是否可用"""
        if self.input_index is not None:
            print(f"麥克風可用，設備索引: {self.input_index}")
            return True
        else:
            print("麥克風不可用")
            return False

    def listen(self, duration=5):
        """錄音並轉換為文字"""
        if self.input_index is None:
            print("STT: 沒有可用的輸入設備")
            return ""
        
        try:
            print(f"開始錄音 {duration} 秒...")
            
            # 取得錄音裝置的採樣率
            devices = sd.query_devices()
            device_info = devices[self.input_index]
            
            # 安全地取得採樣率
            if isinstance(device_info, dict):
                fs = int(device_info.get('default_samplerate', 44100))
            else:
                fs = 44100  # 預設採樣率
                
            print(f"使用採樣率: {fs} Hz")

            # 開始錄音
            recording = sd.rec(
                int(duration * fs), 
                samplerate=fs, 
                channels=1, 
                dtype='int16', 
                device=self.input_index
            )
            sd.wait()
            print("錄音完成，開始轉換...")

            # 儲存成臨時檔案
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            wavfile.write(temp_filename, fs, recording)
            print(f"音檔已儲存: {temp_filename}")

            # 讀取音頻資料給 IBM Watson
            with open(temp_filename, 'rb') as audio_file:
                audio_data = audio_file.read()

            print(f"音檔大小: {len(audio_data)} bytes")

            # IBM Watson 語音轉文字
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type='audio/wav',
                model='en-US_BroadbandModel',
            ).get_result()

            # 清理臨時檔案
            os.unlink(temp_filename)

            # 返回轉錄結果
            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(f"轉錄結果: {transcript}")
                return transcript
            else:
                print("沒有轉錄結果")
                return ""
                
        except Exception as e:
            print(f"STT 錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return ""

    def recognize_audio(self, audio_data, content_type='audio/webm'):
        """識別音訊檔案"""
        try:
            print(f"識別音訊檔案，類型: {content_type}")
            
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type=content_type,
                model='en-US_BroadbandModel',
            ).get_result()

            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(f"識別結果: {transcript}")
                return transcript
            else:
                print("沒有識別結果")
                return ""
                
        except Exception as e:
            print(f"音訊識別錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return ""

    def stop_microphone(self):
        """停止麥克風"""
        try:
            sd.stop()
            print("麥克風已停止")
        except:
            pass