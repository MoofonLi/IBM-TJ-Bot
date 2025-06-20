import os
import subprocess
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)
        self.audio_device = self._detect_audio_device()

    def _detect_audio_device(self):
        """自動偵測第一個可用的音頻設備"""
        try:
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'card' in line and 'device' in line:
                        parts = line.split()
                        card_num = parts[1].rstrip(':')
                        # 找到 device 後面的數字
                        for i, part in enumerate(parts):
                            if part.startswith('device') and i+1 < len(parts):
                                device_num = parts[i+1].rstrip(':')
                                device_id = f"plughw:{card_num},{device_num}"
                                print(f"使用音頻設備: {device_id}")
                                return device_id
        except Exception as e:
            print(f"音頻設備偵測錯誤: {e}")
        
        # 預設值
        print("使用預設音頻設備: plughw:2,0")
        return "plughw:2,0"

    def speak(self, text):
        """使用 IBM Watson Text to Speech 將文字轉為語音並播放"""
        try:
            with open('response.wav', 'wb') as audio_file:
                response = self.text_to_speech.synthesize(
                    text,
                    voice='en-US_AllisonV3Voice',
                    accept='audio/wav'
                ).get_result()
                audio_file.write(response.content)
            print("Audio file saved as response.wav")
            os.system(f"aplay -D {self.audio_device} response.wav")
        except Exception as e:
            print(f"Error in TTS: {e}")