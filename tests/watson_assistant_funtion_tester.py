from utils.watson_assistant import WatsonAssistant
import os
from dotenv import load_dotenv

# 你的 IBM Watson Assistant 和 API 配置信息
assistant_apikey = os.getenv('ASSISTANT_APIKEY')
assistant_url = os.getenv('ASSISTANT_URL')
assistant_id = os.getenv('ASSISTANT_ID')

# 測試與 Watson Assistant 交互的程式
def test_watson_assistant():
    # 初始化 WatsonAssistant 物件
    assistant = WatsonAssistant(assistant_apikey, assistant_url, assistant_id, version='2023-04-15')
    
    # 開始與 Watson Assistant 的對話
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            print("No input detected. Please try again.")
            continue
        
        if "quit" in user_input.lower():
            print("Exiting...")
            break
        
        # 發送訊息到 Watson Assistant
        response = assistant.send_message(user_input)
        
        if response:
            # 提取 Assistant 的回應文本
            response_texts = response.get('output', {}).get('generic', [])
            
            for text in response_texts:
                if text['response_type'] == 'text':
                    print(f"TJBot: {text['text']}")  # 打印 Assistant 的回應
        else:
            print("No response from Assistant.")

# 執行測試
if __name__ == "__main__":
    test_watson_assistant()
