from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class WatsonAssistant:
    def __init__(self, apikey, url, assistant_id, version):
        # 初始化 Watson Assistant 服務
        self.assistant_id = assistant_id
        self.authenticator = IAMAuthenticator(apikey)
        self.assistant = AssistantV2(
            version=version,
            authenticator=self.authenticator
        )
        self.assistant.set_service_url(url)
        self.context = None  # 保存對話的上下文

    def send_message(self, message):
        """與 IBM Watson Assistant 交互，返回回應"""
        try:
            # 構建訊息輸入
            message_input = {
                'message_type': 'text',
                'text': message
            }

            # 發送訊息到 Watson Assistant
            result = self.assistant.message_stateless(
                self.assistant_id,  # 環境ID
                input=message_input,
                context=self.context  # 使用會話上下文來保持會話狀態
            ).get_result()

            # 更新會話上下文
            self.context = result.get('context', None)

            # 返回 Watson Assistant 的回應
            return result

        except Exception as e:
            print(f"Error while sending message to Watson Assistant: {e}")
            return None
