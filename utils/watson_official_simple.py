# Example 2: Adds user input with dotenv for configuration
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 從環境變數讀取 API 金鑰和 URL
assistant_apikey = os.getenv('ASSISTANT_APIKEY')
assistant_url = os.getenv('ASSISTANT_URL')
assistant_id = os.getenv('ASSISTANT_ID')

# Create Assistant service object.
authenticator = IAMAuthenticator(assistant_apikey)
assistant = AssistantV2(
    version = '2023-04-15',
    authenticator = authenticator
)
assistant.set_service_url(assistant_url)

# Initialize with empty value to start the conversation.
message_input = {
    'message_type': 'text',
    'text': ''
    }

context = None

# Main input/output loop
while message_input['text'] != 'quit':

    # Send message to assistant.
    result = assistant.message_stateless(
        assistant_id,
        input = message_input,
        context=context
    ).get_result()
    context = result['context']

    # Print responses from actions, if any. Supports only text responses.
    if result['output']['generic']:
        for response in result['output']['generic']:
            if response['response_type'] == 'text':
                print(response['text'])

    # Prompt for the next round of input unless skip_user_input is True.
    if not result['context']['global']['system'].get('skip_user_input', False):
        user_input = input('>> ')
        message_input = {
            'text': user_input
        }