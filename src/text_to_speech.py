import os
import sounddevice as sd
import scipy.io.wavfile as wavfile
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)
        devices = sd.query_devices()
        self.output_index = None
        for i, device in enumerate(devices):
            if "USB Audio Device" in device['name'] and device['max_output_channels'] > 0:
                output_index = i
                print(f"已自動選擇播放裝置: {device['name']} (index {i})")
                break
        if output_index is None:
            print("沒有找到 USB 音效卡，請確認是否插好。")
        exit(1)
        

    def speak(self, text):
        """使用 IBM Watson Text to Speech 將文字轉為語音並播放"""
        try:
            with open('record.wav', 'wb') as audio_file:
                response = self.text_to_speech.synthesize(
                    text,
                    voice='en-US_AllisonV3Voice',  # 可以更改為其他聲音
                    accept='audio/wav'
                ).get_result()
                audio_file.write(response.content)
            print("Audio file saved as response.wav")
            print("開始播放剛剛的錄音")
            fs2, data = wavfile.read("response.wav")
            sd.play(data, samplerate=fs2, device=self.output_index)
            sd.wait()
            print("播放結束")
        except Exception as e:
            print(f"Error in TTS: {e}")
    