import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class SpeechToText:
    def __init__(self, apikey, url):
        """
        初始化 Speech to Text 服務
        :param apikey: IBM Cloud Speech to Text API 密鑰
        :param url: IBM Cloud Speech to Text 服務 URL
        """
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        self.audio = pyaudio.PyAudio()
        self.stream = None

    def start_microphone(self):
        """初始化麥克風流"""
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )

    def listen(self):
        """
        從麥克風捕捉語音並進行語音轉文字處理
        :return: 轉錄後的文本
        """
        frames = []
        for _ in range(0, int(16000 / 4096 * 5)):  # 捕捉 5 秒音頻
            data = self.stream.read(4096, exception_on_overflow=False)
            frames.append(data)

        audio_data = b''.join(frames)

        try:
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type='audio/l16; rate=16000; channels=1',
                model='en-US_BroadbandModel'
            ).get_result()

            # 提取轉錄文本
            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(f"You said: {transcript}")
                return transcript
            else:
                print("No speech detected.")
                return ""
        except Exception as e:
            print(f"Error during Speech to Text: {e}")
            return ""

    def stop_microphone(self):
        """關閉麥克風流"""
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
