import sounddevice as sd
import scipy.io.wavfile as wavfile
import tempfile
import os
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)
        self.output_index = None
        self._find_speaker()

    def _find_speaker(self):
        """自動尋找 USB Audio Device"""
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if "USB Audio Device" in device['name'] and device['max_output_channels'] > 0:
                self.output_index = i
                break

    def speak(self, text):
        """將文字轉為語音並播放"""
        if self.output_index is None:
            print("No USB Audio Device found")
            return False
            
        try:
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

            # 檢查檔案大小
            file_size = os.path.getsize(temp_filename)
            print(f"Audio file size: {file_size} bytes")
            
            if file_size > 50 * 1024 * 1024:  # 如果檔案超過 50MB
                print("Audio file too large, skipping playback")
                os.unlink(temp_filename)
                return False

            try:
                # 嘗試讀取音檔
                fs, data = wavfile.read(temp_filename)
                print(f"Sample rate: {fs}, Data shape: {data.shape}, Data type: {data.dtype}")
                
                # 檢查資料是否合理
                if len(data) > 10 * fs:  # 如果音頻超過 10 秒
                    print("Audio too long, truncating to 10 seconds")
                    data = data[:10 * fs]
                
                # 播放音頻
                sd.play(data, samplerate=fs, device=self.output_index)
                sd.wait()
                
            except Exception as read_error:
                print(f"Error reading audio file: {read_error}")
                # 清理檔案並返回失敗
                os.unlink(temp_filename)
                return False

            # 清理臨時檔案
            os.unlink(temp_filename)
            
            return True
            
        except Exception as e:
            print(f"Error in TTS: {e}")
            return False