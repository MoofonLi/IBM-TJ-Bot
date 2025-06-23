import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)

    def start_microphone(self):
        """檢查麥克風是否準備好"""
        return True

    def listen(self):
        duration = 5  # 錄音秒數
        filename = "record_test.wav"

        # 列出錄音裝置
        devices = sd.query_devices()
        print("錄音裝置列表")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"{i}: {d['name']}")

        # 自動尋找 USB PnP Sound Device (你的麥克風)
        input_index = None
        for i, device in enumerate(devices):
            if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                input_index = i
                print(f"已自動選擇錄音裝置: {device['name']} (index {i})")
                break

        if input_index is None:
            print("沒有找到 USB 麥克風，請確認是否插好。")
            exit(1)

        # 取得錄音裝置支援的預設採樣率
        fs = int(devices[input_index]['default_samplerate'])

        print("開始錄音")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16', device=input_index)
        sd.wait()
        print("錄音結束")

        # 儲存成 wav
        wavfile.write(filename, fs, recording)
        print(f"錄音已儲存為 {filename}")

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
            print(f"語音識別錯誤: {e}")
            return ""

    def stop_microphone(self):
        """停止麥克風"""
        print("麥克風已停止")