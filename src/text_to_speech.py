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
        """自動偵測可用的音頻設備"""
        try:
            # 列出所有音頻設備
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'card' in line and 'device' in line:
                        # 解析設備資訊，例如: card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]
                        if 'card' in line and 'device' in line:
                            # 提取 card 和 device 編號
                            parts = line.split()
                            card_num = parts[1].rstrip(':')
                            device_num = None
                            for i, part in enumerate(parts):
                                if 'device' in part and i+1 < len(parts):
                                    device_num = parts[i+1].rstrip(':')
                                    break
                            
                            if device_num is not None:
                                device_id = f"plughw:{card_num},{device_num}"
                                # 測試設備是否可用
                                if self._test_audio_device(device_id):
                                    # print(f"找到可用音頻設備: {device_id}")
                                    return device_id
            
            return "plughw:2,0"
            
        except Exception as e:
            print(f"音頻設備偵測錯誤: {e}")
            return "plughw:2,0"  # 預設值

    def _test_audio_device(self, device_id):
        """測試音頻設備是否可用"""
        try:
            # 嘗試播放一個靜音檔案來測試設備
            result = subprocess.run(['aplay', '-D', device_id, '/dev/null'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    def speak(self, text):
        """使用 IBM Watson Text to Speech 將文字轉為語音並播放"""
        try:
            with open('response.wav', 'wb') as audio_file:
                response = self.text_to_speech.synthesize(
                    text,
                    voice='en-US_AllisonV3Voice',  # 可以更改為其他聲音
                    accept='audio/wav'
                ).get_result()
                audio_file.write(response.content)
            # print("Audio file saved as response.wav")
            
            # 使用自動偵測的音頻設備
            os.system(f"aplay -D {self.audio_device} response.wav")
            
        except Exception as e:
            print(f"Error in TTS: {e}")