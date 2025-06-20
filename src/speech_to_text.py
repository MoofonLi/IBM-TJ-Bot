import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        self.audio = pyaudio.PyAudio()
        self.stream = None

    def start_microphone(self):
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=1,  # 強制指定 card 1
                frames_per_buffer=4096
            )
            return True
        except Exception as e:
            return False

    def listen(self):
        """從麥克風捕獲語音並返回轉錄結果"""
        frames = []
        for _ in range(0, int(16000 / 4096 * 5)):  # 捕捉 5 秒音頻
            data = self.stream.read(4096, exception_on_overflow=False)  # 忽略溢出錯誤
            frames.append(data)

        audio_data = b''.join(frames)

        try:
            # 傳送音訊到 IBM Watson Speech to Text
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type='audio/l16; rate=44100; channels=1',
                model='en-US_BroadbandModel',
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

    def recognize_audio(self, audio_data, content_type='audio/webm'):
        """識別音訊檔案"""
        try:
            result = self.speech_to_text.recognize(
                audio=audio_data,
                content_type=content_type,
                model='en-US_BroadbandModel',
            ).get_result()

            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                return transcript
            else:
                return ""
        except Exception as e:
            st.error(f"語音識別錯誤: {e}")
            return ""

    def stop_microphone(self):
        """關閉麥克風流"""
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()