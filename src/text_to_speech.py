import sounddevice as sd
import scipy.io.wavfile as wavfile
import tempfile
import os
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        try:
            print(f"初始化 TTS - API Key前4碼: {apikey[:4] if apikey else 'None'}...")
            print(f"初始化 TTS - URL: {url}")
            
            self.authenticator = IAMAuthenticator(apikey)
            self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
            self.text_to_speech.set_service_url(url)
            self.output_index = None
            
            # 測試連接
            voices = self.text_to_speech.list_voices().get_result()
            print(f"TTS 連接成功，可用語音數量: {len(voices.get('voices', []))}")
            
            self._find_speaker()
            print(f"TTS 初始化完成，音頻輸出設備索引: {self.output_index}")
            
        except Exception as e:
            print(f"TTS 初始化失敗: {e}")
            raise

    def _find_speaker(self):
        """自動尋找可用的音頻輸出設備"""
        try:
            devices = sd.query_devices()
            print(f"偵測到 {len(devices)} 個音頻設備")
            
            # 優先尋找 USB Audio Device
            for i, device in enumerate(devices):
                device_name = str(device.get('name', ''))
                max_output = device.get('max_output_channels', 0)
                
                print(f"設備 {i}: {device_name}, 輸出通道: {max_output}")
                
                if "USB Audio Device" in device_name and max_output > 0:
                    self.output_index = i
                    print(f"找到 USB Audio Device 於索引 {i}")
                    return

            # 如果沒找到 USB Audio Device，使用預設輸出設備
            default_output = sd.query_devices(kind='output')
            if default_output and default_output.get('max_output_channels', 0) > 0:
                # 找到預設輸出設備的索引
                for i, device in enumerate(devices):
                    if device.get('name') == default_output.get('name'):
                        self.output_index = i
                        print(f"使用預設輸出設備: {device.get('name')} (索引 {i})")
                        return
                        
            print("警告: 未找到可用的音頻輸出設備")
            
        except Exception as e:
            print(f"音頻設備檢測錯誤: {e}")
            self.output_index = None

    def speak(self, text):
        """將文字轉為語音並播放"""
        if not text or text.strip() == "":
            print("TTS: 空白文字，跳過語音合成")
            return True
            
        try:
            print(f"TTS 合成文字: {text[:50]}...")
            
            # IBM Watson 文字轉語音
            response = self.text_to_speech.synthesize(
                text,
                voice='en-US_AllisonV3Voice',
                accept='audio/wav'
            ).get_result()

            # 儲存成臨時檔案
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_filename = temp_file.name

            # 讀取音檔
            fs, data = wavfile.read(temp_filename)
            print(f"音檔讀取成功: 採樣率 {fs}, 資料長度 {len(data)}")
            
            # 播放音檔
            if self.output_index is not None:
                print(f"使用設備 {self.output_index} 播放音檔")
                sd.play(data, samplerate=fs, device=self.output_index)
                sd.wait()
            else:
                print("使用預設設備播放音檔")
                sd.play(data, samplerate=fs)
                sd.wait()

            # 清理臨時檔案
            os.unlink(temp_filename)
            print("TTS 播放完成")
            
            return True
            
        except Exception as e:
            print(f"TTS 錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False