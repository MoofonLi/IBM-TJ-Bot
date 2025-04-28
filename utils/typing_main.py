from watson_assistant import WatsonAssistant
from text_to_speech import TextToSpeech
from hardware_control import HardwareControl
import asyncio
from dotenv import load_dotenv
import os

async def main():
    # 配置 IBM Watson 資訊
    assistant_apikey = os.getenv('ASSISTANT_APIKEY')
    assistant_url = os.getenv('ASSISTANT_URL')
    assistant_id = os.getenv('ASSISTANT_ID')

    tts_apikey = os.getenv('TTS_APIKEY')
    tts_url = os.getenv('TTS_URL')


    # 初始化各個模組
    assistant = WatsonAssistant(assistant_apikey, assistant_url, assistant_id, version='2023-04-15')
    tts = TextToSpeech(tts_apikey, tts_url)
    hardware = HardwareControl()

    print("TJBot is ready to interact with you using text and hardware!")
    
    try:
        while True:
            # 使用者文字輸入
            user_input = input("You: ").strip()
            if not user_input:
                print("No input detected. Please try again.")
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
        hardware.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

