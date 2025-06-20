import sounddevice as sd
import scipy.io.wavfile as wavfile
import tempfile
import os
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        self.input_index = None
        self._find_microphone()

    def _find_microphone(self):
        """自動尋找 USB PnP Sound Device"""
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                self.input_index = i
                break

    def start_microphone(self):
        return self.input_index is not None

    def listen(self, duration=5):
        """錄音並轉換為文字"""
        if self.input_index is None:
            return ""
        
        try:
            # 取得錄音裝置支援的預設採樣率
            devices = sd.query_devices()
            fs = int(devices[self.input_index]['default_samplerate'])

            # 開始錄音
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16', device=self.input_index)
            sd.wait()

            # 儲存成臨時檔案
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            wavfile.write(temp_filename, fs, recording)

            # 讀取音頻資料給 IBM Watson
            with open(temp_filename, 'rb') as audio_file:
                audio_data = audio_file.read()

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
                return result['results'][0]['alternatives'][0]['transcript']
            else:
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
                return result['results'][0]['alternatives'][0]['transcript']
            else:
                return ""
        except Exception as e:
            print(f"語音識別錯誤: {e}")
            return ""

    def stop_microphone(self):
        """停止麥克風"""
        pass