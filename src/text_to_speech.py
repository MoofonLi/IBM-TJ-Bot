import os
import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class TextToSpeech:
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.text_to_speech = TextToSpeechV1(authenticator=self.authenticator)
        self.text_to_speech.set_service_url(url)
        
        # 和您的測試代碼一樣，找尋音訊裝置
        devices = sd.query_devices()
        self.output_index = None
        
        # 尋找 USB Audio Device（和您測試代碼邏輯相同）
        for i, device in enumerate(devices):
            if "USB Audio Device" in device['name'] and device['max_output_channels'] > 0:
                self.output_index = i
                print(f"已自動選擇播放裝置: {device['name']} (index {i})")
                break
        
        if self.output_index is None:
            print("沒有找到 USB 音效卡，請確認是否插好。")
            # 使用預設裝置作為備案
            self.output_index = None

    def speak(self, text):
        """使用 IBM Watson Text to Speech 將文字轉為語音並播放"""
        # 使用統一的檔案名（避免之前的檔名不一致問題）
        audio_filename = 'tts_output.wav'
        
        try:
            # 1. 生成音檔（和原始代碼相同）
            print(f"正在生成語音: {text}")
            with open(audio_filename, 'wb') as audio_file:
                response = self.text_to_speech.synthesize(
                    text,
                    voice='en-US_AllisonV3Voice',
                    accept='audio/wav'
                ).get_result()
                audio_file.write(response.content)
            
            print(f"音檔已保存為 {audio_filename}")
            
            # 2. 檢查檔案是否存在且大小合理
            if not os.path.exists(audio_filename):
                print("錯誤：音檔生成失敗")
                return
            
            file_size = os.path.getsize(audio_filename)
            print(f"音檔大小: {file_size} bytes ({file_size/1024:.1f} KB)")
            
            # 檢查檔案大小是否異常（超過 50MB 就很可疑）
            if file_size > 50 * 1024 * 1024:
                print(f"警告：音檔過大 ({file_size/1024/1024:.1f} MB)，可能有問題")
                return
            
            if file_size < 1000:  # 小於 1KB 也很可疑
                print("警告：音檔過小，可能生成失敗")
                return
            
            # 3. 完全按照您的測試代碼邏輯讀取和播放
            print("開始播放語音...")
            fs2, data = wavfile.read(audio_filename)
            
            # 顯示音檔資訊（類似您測試代碼的方式）
            print(f"音檔資訊 - 採樣率: {fs2}Hz, 形狀: {data.shape}, 類型: {data.dtype}")
            
            # 完全按照您的測試代碼播放
            sd.play(data, samplerate=fs2, device=self.output_index)
            sd.wait()
            print("播放結束")
            
        except Exception as e:
            print(f"TTS 播放錯誤: {e}")
            # 嘗試診斷問題
            self._diagnose_audio_file(audio_filename)
        
        finally:
            # 清理音檔（可選，您可以保留檔案用於除錯）
            # if os.path.exists(audio_filename):
            #     os.remove(audio_filename)
            pass

    def _diagnose_audio_file(self, filename):
        """診斷音檔問題"""
        if not os.path.exists(filename):
            print(f"檔案 {filename} 不存在")
            return
        
        print(f"診斷檔案: {filename}")
        print(f"檔案大小: {os.path.getsize(filename)} bytes")
        
        # 讀取檔案前幾個位元組檢查格式
        try:
            with open(filename, 'rb') as f:
                header = f.read(16)
                print(f"檔案開頭: {header}")
                
                # 檢查是否為 WAV 格式
                if header.startswith(b'RIFF') and b'WAVE' in header:
                    print("檔案格式：WAV ✓")
                else:
                    print("檔案格式：不是標準 WAV 格式 ✗")
                    
        except Exception as e:
            print(f"檔案診斷失敗: {e}")

    def test_devices(self):
        """測試音訊裝置（仿照您的測試代碼）"""
        devices = sd.query_devices()
        print("音訊裝置列表:")
        
        print("\n輸入裝置 (麥克風):")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"{i}: {d['name']}")
        
        print("\n輸出裝置 (喇叭):")
        for i, d in enumerate(devices):
            if d['max_output_channels'] > 0:
                print(f"{i}: {d['name']}")
        
        print(f"\n當前選擇的輸出裝置: {self.output_index}")

    def test_tts(self):
        """測試 TTS 功能"""
        test_text = "Hello, this is a test."
        print("測試 TTS 功能...")
        self.speak(test_text)