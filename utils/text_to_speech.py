import os
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)

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
            print("Audio file saved as response.wav")
            os.system("aplay response.wav")  # 播放音訊
        except Exception as e:
            print(f"Error in TTS: {e}")
