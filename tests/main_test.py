from src.watson_assistant import WatsonAssistant
from src.text_to_speech import TextToSpeech
from src.hardware_control import HardwareControl
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pyaudio
import asyncio
import os
from dotenv import load_dotenv

class SpeechToText:
    def __init__(self, apikey, url):
        # 初始化 Speech to Text 服務
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
            rate=44100,
            input=True,
            input_device_index=1,   # <<<< 新增這一行，強制指定 card 1
            frames_per_buffer=4096
        )

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

    def stop_microphone(self):
        """關閉麥克風流"""
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

async def main():
    # 從環境變數讀取 IBM Watson 資訊
    assistant_apikey = os.getenv('ASSISTANT_APIKEY')
    assistant_url = os.getenv('ASSISTANT_URL')
    assistant_id = os.getenv('ASSISTANT_ID')

    tts_apikey = os.getenv('TTS_APIKEY')
    tts_url = os.getenv('TTS_URL')

    stt_apikey = os.getenv('STT_APIKEY')
    stt_url = os.getenv('STT_URL')

    # 初始化各個模組
    assistant = WatsonAssistant(assistant_apikey, assistant_url, assistant_id, version='2023-04-15')
    tts = TextToSpeech(tts_apikey, tts_url)
    stt = SpeechToText(stt_apikey, stt_url)
    hardware = HardwareControl()

    print("TJBot is ready to interact with you using voice and hardware!")
    stt.start_microphone()

    try:
        while True:
            # 從麥克風捕獲語音並轉錄
            print("Listening for your command...")
            user_input = stt.listen().strip()
            if not user_input:
                continue

            if "stop" in user_input.lower():
                print("Stopping...")
                break

            # 發送訊息到 Assistant 並獲取回應
            response = assistant.send_message(user_input)
            if response:
                intents = response.get('output', {}).get('intents', [])
                entities = response.get('output', {}).get('entities', [])
                response_texts = response.get('output', {}).get('generic', [])

                for text in response_texts:
                    if text['response_type'] == 'text':
                        print(f"TJBot: {text['text']}")
                        tts.speak(text['text'])  # 語音回應

                # 處理 Assistant 的意圖
                if intents:
                    top_intent = intents[0]['intent']
                    if top_intent == 'wave':
                        hardware.wave()
                    elif top_intent == 'lower-arm':
                        hardware.lower_arm()
                    elif top_intent == 'raise-arm':
                        hardware.raise_arm()
                    elif top_intent == 'shine':
                        # 從 entities 提取顏色
                        color = next((e['value'] for e in entities if e['entity'] == 'color'), 'white')
                        hardware.shine(color)
            else:
                print("No response from Assistant.")

    except KeyboardInterrupt:
        print("Program terminated by user.")
    finally:
        stt.stop_microphone()
        hardware.cleanup()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())