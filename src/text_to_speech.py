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

            # 讀取音檔並播放
            fs, data = wavfile.read(temp_filename)
            sd.play(data, samplerate=fs, device=self.output_index)
            sd.wait()

            # 清理臨時檔案
            os.unlink(temp_filename)
            
            return True
            
        except Exception as e:
            print(f"Error in TTS: {e}")
            return False