import sounddevice as sd
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import io
import wave

class SpeechToText:
    def __init__(self, apikey, url):
        authenticator = IAMAuthenticator(apikey)
        self.speech_to_text = SpeechToTextV1(authenticator=authenticator)
        self.speech_to_text.set_service_url(url)
        self.input_device_index = None
        self.sample_rate = 16000  # Watson STT 建議使用 16kHz
        
    def start_microphone(self):
        """尋找並設定 USB 麥克風"""
        try:
            # 列出所有音訊設備
            devices = sd.query_devices()
            print("可用的音訊設備：")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"{i}: {device['name']} - 輸入通道: {device['max_input_channels']}")
            
            # 自動尋找 USB PnP Sound Device (你的麥克風)
            self.input_device_index = None
            for i, device in enumerate(devices):
                if "USB PnP Sound Device" in device['name'] and device['max_input_channels'] > 0:
                    self.input_device_index = i
                    print(f"已選擇錄音裝置: {device['name']} (index {i})")
                    break
            
            # 如果沒找到 USB PnP Sound Device，尋找其他 USB 麥克風
            if self.input_device_index is None:
                for i, device in enumerate(devices):
                    if ("USB" in device['name'] or "Microphone" in device['name']) and device['max_input_channels'] > 0:
                        self.input_device_index = i
                        print(f"已選擇錄音裝置: {device['name']} (index {i})")
                        break
            
            # 如果還是沒找到，使用預設設備
            if self.input_device_index is None:
                self.input_device_index = sd.default.device[0]
                print(f"使用預設錄音設備 (index {self.input_device_index})")
            
            print(f"使用採樣率: {self.sample_rate} Hz")
            return True
                
        except Exception as e:
            print(f"Error setting up microphone: {e}")
            return False

    def listen(self, duration=5):
        """從麥克風捕獲語音並返回轉錄結果"""
        if self.input_device_index is None:
            print("麥克風未初始化，請先呼叫 start_microphone()")
            return ""
        
        try:
            print(f"開始錄音 {duration} 秒...")
            
            # 使用 sounddevice 錄音
            recording = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype='int16', 
                device=self.input_device_index
            )
            sd.wait()  # 等待錄音完成
            
            print("錄音結束，正在處理...")
            
            # 檢查音訊數據品質
            max_amplitude = np.max(np.abs(recording))
            print(f"錄音最大振幅: {max_amplitude}")
            
            if max_amplitude < 100:  # 如果音訊太小
                print("警告：錄音音量很低，可能需要調整麥克風音量")
            
            # 將錄音轉換為 WAV 格式
            wav_buffer = self._convert_to_wav(recording, self.sample_rate)
            
            # 傳送音訊到 IBM Watson Speech to Text
            result = self.speech_to_text.recognize(
                audio=wav_buffer,
                content_type='audio/wav',
                model='en-US_BroadbandModel',
                keywords=['hello', 'hi', 'robot', 'wave', 'light', 'arm'],  # 添加關鍵字
                keywords_threshold=0.5,
                max_alternatives=3,
                word_confidence=True
            ).get_result()
            
            print(f"Watson STT 回應: {result}")

            # 提取轉錄文本
            if 'results' in result and len(result['results']) > 0:
                alternatives = result['results'][0]['alternatives']
                if alternatives:
                    transcript = alternatives[0]['transcript'].strip()
                    confidence = alternatives[0].get('confidence', 0)
                    print(f"識別結果: {transcript} (信心度: {confidence})")
                    
                    # 如果信心度太低，返回空字串
                    if confidence < 0.3:
                        print("信心度太低，忽略此結果")
                        return ""
                    
                    return transcript
                else:
                    print("沒有找到替代方案")
                    return ""
            else:
                print("沒有檢測到語音或結果為空")
                return ""
                
        except Exception as e:
            print(f"Error during Speech to Text: {e}")
            return ""

    def _convert_to_wav(self, recording, sample_rate):
        """將錄音轉換為 WAV 格式"""
        wav_buffer = io.BytesIO()
        
        # 創建 WAV 文件
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 單聲道
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(recording.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer

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
        """停止麥克風（sounddevice 不需要手動停止）"""
        print("麥克風已停止")
        pass

    def test_recording(self, duration=3):
        """測試錄音功能"""
        print("=== 語音識別測試 ===")
        
        if not self.start_microphone():
            print("測試失敗：無法初始化麥克風")
            return False
            
        print(f"測試錄音 {duration} 秒...")
        result = self.listen(duration)
        
        if result:
            print(f"測試成功！識別結果: '{result}'")
            return True
        else:
            print("測試完成，但沒有識別到語音")
            print("建議檢查：")
            print("1. 麥克風是否正常工作")
            print("2. 麥克風音量設定")
            print("3. 說話時是否靠近麥克風")
            print("4. 網路連線是否正常")
            return False

    def list_audio_devices(self):
        """列出所有音訊設備"""
        print("=== 音訊設備列表 ===")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            device_type = "輸入" if device['max_input_channels'] > 0 else "輸出"
            if device['max_input_channels'] > 0:
                print(f"{i}: {device['name']} ({device_type}) - 通道: {device['max_input_channels']}")
        return devices